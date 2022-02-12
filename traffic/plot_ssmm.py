import json
from matplotlib import pyplot as plt

def load_json(path):
    with open(path, "r") as fin:
        data = json.load(fin)
    
    return data

def normalize_timestamps(timestamps, offset):
    norm_timestamps = list()

    for ts in timestamps:
        norm_timestamps.append((ts - offset) * 100)

    return norm_timestamps    

def plot_ssmm_traffic(timestamps_pu, bytes_pu, timestamps_ed, bytes_ed, timestamps_pe, bytes_pe):
    markerline_pu, _, _ = plt.stem(timestamps_pu, bytes_pu, bottom=-3)
    markerline_ed, _, _ = plt.stem(timestamps_ed, bytes_ed, bottom=-3, markerfmt="C1o", linefmt="C1-")
    
    e = 0
    for pe in bytes_pe:
        for b in pe:
            markerline_pe, _, _ = plt.stem(timestamps_pe[e], b, bottom=-3, markerfmt="C2o", linefmt="C2--")
            markerline_pe.set_markerfacecolor("none")
            plt.setp(markerline_pe, markersize=6)
        e += 1
        
    markerline_pu.set_markerfacecolor("none")
    plt.setp(markerline_pu, markersize=7)
    markerline_ed.set_markerfacecolor("none")
    plt.setp(markerline_ed, markersize=10)

    plt.ylim(0, 1500)
    plt.xlabel("Time (s)")
    plt.ylabel("Message length (bytes)")
    plt.legend(["Periodic update", "Event detection", "Payload exchange"], ncol=3, loc="lower center", bbox_to_anchor=[0.5, -0.25])
    plt.tight_layout()
    plt.savefig("plot_ssmm.png")
    plt.close()


if __name__ == "__main__":
    path = "events_ssmm.json"
    
    events = load_json(path)

    timestamps_pu = list()
    bytes_pu = list()
    timestamps_ed = list()
    bytes_ed = list()
    timestamps_pe = list()
    bytes_pe = list()
    for e in events:
        if e["event"] == "pe":
            timestamps_pe.append(e["ts"])
            bytes_pe.append(e["bytes"])
        elif e["event"] == "pu":
            timestamps_pu.append(e["ts"])
            bytes_pu.append(e["bytes"])
        else:
            timestamps_ed.append(e["ts"])
            bytes_ed.append(e["bytes"])

    time_offset = timestamps_pu[0]

    timestamps_pu = normalize_timestamps(timestamps_pu, time_offset)
    timestamps_pe = normalize_timestamps(timestamps_pe, time_offset)
    timestamps_ed = normalize_timestamps(timestamps_ed, time_offset)

    plot_ssmm_traffic(timestamps_pu, bytes_pu, timestamps_ed, bytes_ed, timestamps_pe, bytes_pe)
