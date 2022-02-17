import argparse
import time
import json
import shlex
import random
import subprocess
import numpy as np
import psutil


random.seed(time.time())

event_json = list()

def store_list_as_json(filename, data):
    with open(filename, "w") as fout:
        json.dump(data, fout, indent=2)
        fout.write("\n")

def log_event(event, bytes):
    event_data = {
        "event": event,
        "ts": time.time(),
        "bytes": bytes
    }

    event_json.append(event_data)

def get_tun_ip():
    ifs = psutil.net_if_addrs()

    while g_tun_name not in ifs:
        time.sleep(1)
        ifs = psutil.net_if_addrs()

    print(f"{g_tun_name} is up")

    tun_if = ifs[g_tun_name]
    return tun_if[0].address

def register_ue(conf):
    if not conf["dry_run"] and not conf["ue_registered"]:
        global g_tun_ip

        cmd = "./nr-cli imsi-901700000000001 --exec 'ps-establish IPv4 --sst 1 --sd 1 --dnn internet'"
        cmd = shlex.split(cmd)
        ret = subprocess.run(cmd)
        conf["ue_registered"] = True

        print("Waiting for tun interface...")
        g_tun_ip = get_tun_ip()

def run_iperf(transmit_rate, transmit_bytes=None, transmit_time=None):
    if conf["dry_run"]:
        return None

    if transmit_bytes is not None:
        cmd = f"iperf3 -c {g_server_ip} -B {g_tun_ip} -n {transmit_bytes} b {transmit_rate}"
    elif transmit_time is not None:
        cmd = f"iperf3 -c {g_server_ip} -B {g_tun_ip} -t {transmit_time} b {transmit_rate}"
    else:
        print("ERR: iperf3 needs either transmit_bytes or transmit_time to run")

    cmd = shlex.split(cmd)
    return subprocess.run(cmd)

# Packet length distribution following IMIX
def get_total_bytes():
    num = random.random()
    if num < 0.58:
        return 64
    elif num < 0.91:
        return 580
    else:
        return 1400


def off(conf=None):
    print("off")
    if not conf["dry_run"] and conf["ue_registered"]:
        cmd = "./nr-cli imsi-901700000000001 --exec 'deregister disable-5g'"
        cmd = shlex.split(cmd)
        ret = subprocess.run(cmd)
        conf["ue_registered"] = False

    log_event("off", None)

# Let event detection happen after this state as well. Very small probability though
def periodic_update(conf):
    register_ue(conf)

    transmit_rate = conf["rate_pu"]
    transmit_bytes = conf["bytes_pu"]

    print(f"periodic update: rate {transmit_rate}, bytes: {transmit_bytes}")
    run_iperf(transmit_rate, transmit_bytes)

    log_event("pu", transmit_bytes)

# Maybe try to modify bearer for fast transmission
def event_driven(conf):
    register_ue(conf)

    transmit_rate = conf["rate_ed"]
    transmit_bytes = get_total_bytes()

    print(f"event driven: rate {transmit_rate}, bytes: {transmit_bytes}")
    run_iperf(transmit_rate, transmit_bytes)

    log_event("ed", transmit_bytes)

def payload_exchange(conf):
    register_ue(conf)

    trasnmit_rate = conf["rate_pe"]

    # Send several burst with payload sizes distributed according to IMIX
    print(f"payload exchange: rate {trasnmit_rate}")
    transmit_bytes_list = list()
    for burst in range(10):
        transmit_bytes = get_total_bytes()
        transmit_bytes_list.append(transmit_bytes)
        run_iperf(trasnmit_rate, transmit_bytes)

    log_event("pe", transmit_bytes_list)

g_state_table = {
    0: off,
    1: periodic_update,
    2: event_driven,
    3: payload_exchange,
}

def multinomial(v):
    r = np.random.uniform(0.0, 1.0)
    CS = np.cumsum(v)
    CS = np.insert(CS, 0, 0)
    m = (np.where(CS<r))[0]
    next_state=m[len(m)-1]
    
    return next_state

def run(P, state, conf):
    start = (np.where(state>0))[1]
    current_state = start[0]
    state_hist = state
    timestamp_next_pu = time.time() + conf["sojourn_time_pu"]

    for x in range(conf["num_it"]):
        current_row = np.ma.masked_values((P[current_state]), 0.0)
        next_state = multinomial(current_row)

        state = np.array([[0, 0, 0, 0]])
        state[0, next_state] = 1.0

        # Sojourn if we're in OFF state
        if next_state == 1:
            time_to_sleep = timestamp_next_pu - time.time()
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
            else:
                print(f"Missed pu by {time_to_sleep * -1} seconds")
            timestamp_next_pu += conf["sojourn_time_pu"]
        elif next_state == 2:
            sojourn_ed = random.expovariate(conf["lam_ed"])
            time_until_pu = timestamp_next_pu - time.time()
            # Don't miss an entire PU because of an ED
            if sojourn_ed > time_until_pu:
                sojourn_ed = time_until_pu

            # We don't wanna delay the next PU just because of an ED
            # time_until_pu -= sojourn_ed

            if sojourn_ed > 0:
                time.sleep(sojourn_ed)

        s = g_state_table[next_state]
        s(conf)

        state_hist = np.append(state_hist, state, axis=0)
        current_state = next_state

    store_list_as_json(conf["filepath"], event_json)

    print("state histogram\n", state_hist)


# Todo: For real measurements change @-t_pu=600 (10min), @-l_ed=0.005
if __name__ == "__main__":
    global g_tun_name
    global g_tun_ip
    global g_server_ip

    P = np.array([[0, 0.9, 0.1, 0],
                  [1, 0, 0, 0],
                  [0.3, 0, 0, 0.7],
                  [1, 0, 0, 0]])
    state = np.array([[1.0, 0, 0, 0]])

    parser = argparse.ArgumentParser()

    parser.add_argument("-i",
                        default=20,
                        const=20,
                        nargs="?",
                        type=int,
                        help="number of iterations")
    parser.add_argument("-t_pu",
                        default=10.0,
                        const=10.0,
                        nargs="?",
                        type=float,
                        help="sojourn time between PUs [s]")
    parser.add_argument("-t_tran",
                        default=1,
                        const=1,
                        nargs="?",
                        type=int,
                        help="transmission time for PU and ED [s]")
    parser.add_argument("-r_pu",
                        default=10000,
                        const=10000,
                        nargs="?",
                        type=int,
                        help="rate for PU traffic [bit/s]")
    parser.add_argument("-r_ed",
                        default=10000,
                        const=10000,
                        nargs="?",
                        type=int,
                        help="rate for ED traffic [bit/s]")
    parser.add_argument("-r_pe",
                        default=1000000,
                        const=1000000,
                        nargs="?",
                        type=int,
                        help="rate for PE traffic [bit/s]")
    parser.add_argument("b_pu",
                        default=100,
                        const=100,
                        nargs="?",
                        type=int,
                        help="number of bytes to tranmit for a peridoc update")
    parser.add_argument("-l_ed",
                        default=0.3,
                        const=0.4,
                        nargs="?",
                        type=float,
                        help="lambda for sojourn time before ED")
    parser.add_argument("-l_pe",
                        default=0.05,
                        const=0.05,
                        nargs="?",
                        type=float,
                        help="lambda for transmission time for PE")
    parser.add_argument("-s",
                        default="10.45.0.1",
                        const="10.45.0.1",
                        nargs="?",
                        type=str,
                        help="ipv4 address of the iperf3 server")
    parser.add_argument("-c",
                        default="10.45.0.2",
                        const="10.45.0.2",
                        nargs="?",
                        type=str,
                        help="ipv4 address of the iperf3 client")
    parser.add_argument("-d",
                        default="uesimtun0",
                        const="uesimtun0",
                        nargs="?",
                        type=str,
                        help="device name of the tun interface")
    parser.add_argument("-o",
                        default="events_ssmm.json",
                        const="events_ssmm.json",
                        nargs="?",
                        type=str,
                        help="path to the outfile")
    parser.add_argument("--dry-run",
                        action='store_true',
                        help="don't perform registration and transmission")
    args = parser.parse_args()

    conf = {
        "num_it": args.i,
        "sojourn_time_pu": args.t_pu,
        "transmit_time": args.t_tran,
        "rate_pu": args.r_pu,
        "rate_ed": args.r_ed,
        "rate_pe": args.r_pe,
        "bytes_pu": args.b_pu,
        "lam_ed": args.l_ed,
        "lam_pe": args.l_pe,
        "server_addr": args.s,
        "client_addr": args.c,
        "ue_registered": True,
        "filepath": args.o,
        "dry_run": args.dry_run
    }

    g_tun_name = args.d
    g_server_ip = args.s
    if not conf["dry_run"]:
        g_tun_ip = get_tun_ip()

    run(P, state, conf)
