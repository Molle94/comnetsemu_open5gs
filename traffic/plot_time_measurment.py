import json
from datetime import datetime

from cycler import cycler
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib.ticker as plticker
from mpl_toolkits.axes_grid1 import make_axes_locatable

from plotting import setup

GLOBAL_EVENT_ORDER = ['read', 'write', 'new', 'init', 'clear']  # 'time',


def load_json(path):
    with open(path, "r") as fin:
        data = json.load(fin)

    return data

if __name__ == "__main__":
    path_state = "../analyse/instrumentation-data-20220504-104207.742000.json"

    state = load_json(path_state)

    # figwidth = plt.rcParams['figure.figsize'][0]
    # figheight = figwidth * (sum([1 for function in state if not function.startswith("__")]) + 1) * 0.5
    # setup(height=(sum([1 for function in state if not function.startswith("__")]) + 1) * 2, span=True)
    # fig, ax = plt.subplots(1)
    # # fig.tight_layout()
    # print(sum([1 for function in state if not function.startswith("__")]) + 1)
    # divider = make_axes_locatable(ax)

    # state_ax = ax
    if "ausf" in state:
        times = []
        for fun in state["ausf"]["time"]:
            if fun.startswith("time_"):
                for t in state["ausf"]["time"][fun]:
                    times.append((fun, t["duration"], t["timestamp"]))

    del state

    df = pd.DataFrame(data=times, columns=("function", "duration", "timestamp"))

    sns.catplot(x="function", y="duration", kind="box", data=df[df["duration"] < 10000])

    print(df.groupby("function").mean())

    plt.savefig(f"plot_time_box_20220504.png")

    exit()

    for function in state:
        if function.startswith("__"):
            continue

        state_ax = divider.append_axes("bottom", "50%", sharex=state_ax)

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
                ts = state_event_timestamp.get(event["event"], [])
                ts.append(datetime.fromisoformat(event['timestamp']))
                state_event_timestamp[event["event"]] = ts
                state_event.append(event["event"])

            for child in state[function]["state_changes"][states]["child_events"]:
                for event in state[function]["state_changes"][states]["child_events"][child]["events"]:
                    ts = state_event_timestamp.get(event["event"], [])
                    ts.append(datetime.fromisoformat(event['timestamp']))
                    state_event_timestamp[event["event"]] = ts
                    state_event.append(event["event"])

        for event in state_event_timestamp:
            state_event_timestamp[event] = list(normalize_datetimes(state_event_timestamp[event], datetime_offset))
        print(state_event_timestamp)

        plot_state(state_event_timestamp, state_event, ax=state_ax, nf=function)

    plt.xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(f"plot_ssmm_combined_{datetime_offset.strftime('%Y%m%d%H%M')}.png")
    plt.close()