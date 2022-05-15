import json
from datetime import datetime

from cycler import cycler
from matplotlib import pyplot as plt
import matplotlib.ticker as plticker
from mpl_toolkits.axes_grid1 import make_axes_locatable

from plotting import setup

GLOBAL_EVENT_ORDER = ['read', 'write', 'new', 'init', 'clear'] #'time',
SUFFIX = "pdf"
LOC_BASE = 30
EVENT_MAP = {"clear": "write", "init": "write", "new": "write"}

def load_json(path):
    with open(path, "r") as fin:
        data = json.load(fin)
    
    return data


def normalize_timestamps(timestamps, offset):
    norm_timestamps = list()

    for ts in timestamps:
        norm_timestamps.append((ts - offset) ) # * 100

    return norm_timestamps


def normalize_datetimes(datetimes, offset):
    for dt in datetimes:
        yield (dt - offset).total_seconds()


def plot_ssmm_traffic(timestamps_pu, bytes_pu, timestamps_ed, bytes_ed, timestamps_pe, bytes_pe, ax=None, xlim=None):
    if ax is None:
        ax = plt.axes()

    if xlim is not None:
        plt.xlim(xlim)

    loc = plticker.MultipleLocator(base=LOC_BASE)  # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)

    markerline_pu, _, _ = ax.stem(timestamps_pu, bytes_pu, bottom=-3)
    if timestamps_pe:
        markerline_ed, _, _ = ax.stem(timestamps_ed, bytes_ed, bottom=-3, markerfmt="C1o", linefmt="C1-")
    else:
        markerline_ed = None
    
    e = 0
    for pe in bytes_pe:
        for b in pe:
            markerline_pe, _, _ = ax.stem(timestamps_pe[e], b, bottom=-3, markerfmt="C2o", linefmt="C2--")
            markerline_pe.set_markerfacecolor("none")
            plt.setp(markerline_pe, markersize=6)
        e += 1
        
    markerline_pu.set_markerfacecolor("none")
    plt.setp(markerline_pu, markersize=7)
    if markerline_ed:
        markerline_ed.set_markerfacecolor("none")
        plt.setp(markerline_ed, markersize=10)

    plt.ylim(0, 1500)
    plt.xlabel("Time (s)")
    plt.ylabel("Message length (bytes)")
    ax.legend(["Periodic update", "Event detection", "Payload exchange"], loc="best") #, bbox_to_anchor=[0.5, -0.1]) # , title=f"UE Traffic"
    # plt.title(f"UE Traffic")
    plt.tight_layout()
    plt.savefig(f"plot_ssmm_traffic_{datetime_offset.strftime('%Y%m%d%H%M')}.{SUFFIX}")
    plt.close()


def plot_state(state_timestamps, state_event, ax=None, nf=None, xlim=None):
    if ax is None:
        ax = plt.axes()

    if xlim is not None:
        plt.xlim(xlim)

    loc = plticker.MultipleLocator(base=LOC_BASE)  # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)

    # distinct_events = list()
    distinct_events = [e for e in GLOBAL_EVENT_ORDER if e in set(state_event)]

    print(f"Events not showen: {set(state_event) - set(distinct_events)}")

    custom_cycler = (cycler(color=['#00305d', '#ef7d00', '#65b32e']) + cycler(marker=["+", "x", "o"]) * cycler(linestyle=['none']))
    ax.set_prop_cycle(custom_cycler)

    for event in distinct_events:
        # if event in distinct_events:
        markerline_pu = ax.plot(state_timestamps[event], [distinct_events.index(event) + 1 for _ in state_timestamps[event]]) # bottom=-3)
        plt.setp(markerline_pu, markersize=7)

    plt.ylim(0, len(distinct_events) + 1)
    # states = ", ".join([f"{i + 1}: {state}" for i, state in enumerate(distinct_events)])
    plt.ylabel(f"Events")
    plt.xlabel("Time (s)")
    plt.yticks(range(len(distinct_events)+1), [""] + distinct_events)
    title = None
    if nf is not None:
        #     plt.title(f"State events for NF {nf}")
        title = f"NF {nf}"
    # plt.legend(distinct_events, ncol=len(distinct_events), loc="best", title=title)
               # bbox_to_anchor=[0.5, -0.75])

    plt.tight_layout()
    plt.savefig(f"plot_ssmm_state_{nf}_{datetime_offset.strftime('%Y%m%d%H%M')}.{SUFFIX}")
    plt.close()


if __name__ == "__main__":
    path = "../events_ssmm-202204281121.json"
    path_state = "../analyse/instrumentation-data-20220428-112113.761000.json"
    
    events = load_json(path)
    state = load_json(path_state)

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
        elif e["event"] == "ed":
            timestamps_ed.append(e["ts"])
            bytes_ed.append(e["bytes"])

    time_offset = timestamps_pu[0]
    if len(timestamps_ed) > 0 and timestamps_ed[0] < time_offset:
        time_offset =  timestamps_ed[0]

    if len(timestamps_pe) > 0 and timestamps_pe[0] < time_offset:
        time_offset =  timestamps_pe[0]

    timestamps_pu = normalize_timestamps(timestamps_pu, time_offset)
    timestamps_pe = normalize_timestamps(timestamps_pe, time_offset)
    timestamps_ed = normalize_timestamps(timestamps_ed, time_offset)

    xmin = min(min(timestamps_pu), min(timestamps_ed), min(timestamps_pe))
    xmax = max(max(timestamps_pu), max(timestamps_ed), max(timestamps_pe))

    datetime_offset = datetime.utcfromtimestamp(time_offset)


    # figwidth = plt.rcParams['figure.figsize'][0]
    # figheight = figwidth * (sum([1 for function in state if not function.startswith("__")]) + 1) * 0.5
    setup(height=3, span=True)

    # fig, ax = plt.subplots(1)
    # fig.tight_layout()
    print(sum([1 for function in state if not function.startswith("__")]) + 1)
    # divider = make_axes_locatable(ax)

    # state_ax = ax
    state_plots = []
    for function in state:
        if function.startswith("__"):
            continue

        # state_ax = divider.append_axes("bottom", "50%", sharex=state_ax)

        state_event = []
        state_event_timestamp = {}

        for times in state[function]["time"]:
            for event in state[function]["time"][times]:
                ts = state_event_timestamp.get("time", [])
                ts.append(datetime.fromisoformat(event['timestamp']))
                state_event_timestamp["time"] = ts
                state_event.append("time")

        for states in state[function]["state_changes"]:
            for event in state[function]["state_changes"][states]["events"]:
                mapped_event = EVENT_MAP.get(event["event"], event["event"])
                ts = state_event_timestamp.get(mapped_event, [])
                ts.append(datetime.fromisoformat(event['timestamp']))
                state_event_timestamp[mapped_event] = ts
                state_event.append(mapped_event)

            for child in state[function]["state_changes"][states]["child_events"]:
                for event in state[function]["state_changes"][states]["child_events"][child]["events"]:
                    mapped_event = EVENT_MAP.get(event["event"], event["event"])
                    ts = state_event_timestamp.get(mapped_event, [])
                    ts.append(datetime.fromisoformat(event['timestamp']))
                    state_event_timestamp[mapped_event] = ts
                    state_event.append(mapped_event)

        for event in state_event_timestamp:
            state_event_timestamp[event] = list(normalize_datetimes(state_event_timestamp[event], datetime_offset))
            xmin = min(xmin, min(state_event_timestamp[event]))
            xmax = max(xmax, max(state_event_timestamp[event]))

        print(state_event_timestamp)

        state_plots.append((state_event_timestamp, state_event, function))

    print(xmin)
    print(xmax)
    xmin -= (xmin % LOC_BASE)
    xmax += LOC_BASE - (xmax % LOC_BASE)
    print(xmin)
    print(xmax)

    plot_ssmm_traffic(timestamps_pu, bytes_pu, timestamps_ed, bytes_ed, timestamps_pe, bytes_pe, ax=None, xlim=[xmin, xmax])

    setup(height=2, span=True)
    for state_event_timestamp, state_event, function in state_plots:
        plot_state(state_event_timestamp, state_event, ax=None, nf=function, xlim=[xmin, xmax])

    plt.xlabel("Time (s)")
    plt.tight_layout()
    plt.savefig(f"plot_ssmm_combined_{datetime_offset.strftime('%Y%m%d%H%M')}.png")
    plt.close()
