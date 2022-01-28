import argparse
import time
import shlex
import random
import subprocess
import numpy as np


random.seed(time.time())

def off(conf=None):
    print("")

# Let event detection happen after this state as well. Very small probability though
def periodic_update(conf):
    rate = conf["rate_pu"]
    transmit_time = conf["transmit_time"]

    cmd = f"iperf3 -c {g_server_ip} -B {g_tun_ip} -t {transmit_time} -b {rate}"
    cmd = shlex.split(cmd)
    ret = subprocess.run(cmd)

# Maybe try to modify bearer for fast transmission
def event_driven(conf):
    rate = conf["rate_ed"]
    transmit_time = conf["transmit_time"]

    cmd = f"iperf3 -c {g_server_ip} -B {g_tun_ip} -t {transmit_time} -b {rate}"
    cmd = shlex.split(cmd)
    ret = subprocess.run(cmd)

def payload_exchange(conf):
    rate = conf["rate_pe"]
    time_pe = random.expovariate(conf["lam_pe"])

    cmd = f"iperf3 -c {g_server_ip} -B {g_tun_ip} -t {time_pe} -b {rate}"
    cmd = shlex.split(cmd)
    ret = subprocess.run(cmd)


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

    for x in range(conf["num_it"]):
        current_row = np.ma.masked_values((P[current_state]), 0.0)
        next_state = multinomial(current_row)

        state = np.array([[0, 0, 0, 0]])
        state[0, next_state] = 1.0

        # Sojourn if we're in OFF state
        if next_state == 1:
            time.sleep(conf["sojourn_time_pu"])
        elif next_state == 2:
            sojourn_ed = random.expovariate(conf["lam_ed"])
            time.sleep(sojourn_ed)

        s = g_state_table[next_state]
        s(conf)

        state_hist = np.append(state_hist, state, axis=0)
        current_state = next_state

    print("state histogram\n", state_hist)


# Todo (Malte): Add num_bits as args for iperf3
if __name__ == "__main__":
    global g_server_ip
    global g_tun_ip

    P = np.array([[0, 0.7, 0.3, 0],
                  [1, 0, 0, 0],
                  [0.4, 0, 0, 0.6],
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
                        default=1.0,
                        const=1.0,
                        nargs="?",
                        type=float,
                        help="sojourn time between PUs")
    parser.add_argument("-t_tran",
                        default=1,
                        const=1,
                        nargs="?",
                        type=int,
                        help="transmission time for PU and ED")
    parser.add_argument("-r_pu",
                        default=1000,
                        const=1000,
                        nargs="?",
                        type=int,
                        help="rate for PU traffic [bit/s]")
    parser.add_argument("-r_ed",
                        default=1000,
                        const=1000,
                        nargs="?",
                        type=int,
                        help="rate for ED traffic [bit/s]")
    parser.add_argument("-r_pe",
                        default=10000,
                        const=10000,
                        nargs="?",
                        type=int,
                        help="rate for PE traffic [bit/s]")
    parser.add_argument("-l_ed",
                        default=0.4,
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
    args = parser.parse_args()

    conf = {
        "num_it": args.i,
        "sojourn_time_pu": args.t_pu,
        "transmit_time": args.t_tran,
        "rate_pu": args.r_pu,
        "rate_ed": args.r_ed,
        "rate_pe": args.r_pe,
        "lam_ed": args.l_ed,
        "lam_pe": args.l_pe,
        "server_addr": args.s,
        "client_addr": args.c,
    }

    g_server_ip = args.s
    g_tun_ip = args.c

    run(P, state, conf)
