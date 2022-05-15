import json
import pathlib
from datetime import datetime

import click

EVENT_MAP = {"clear": "write", "init": "write", "new": "write"}


def load_json(path):
    with open(path, "r") as fin:
        data = json.load(fin)

    return data


def print_callstack(nf_data):
    timeline_of_events = []

    for state in nf_data["state_changes"]:
        for event in nf_data["state_changes"][state]["events"]:
            mapped_event = EVENT_MAP.get(event["event"], event["event"])
            timeline_of_events.append({
                "timestamp": datetime.fromisoformat(event['timestamp']),
                "type": "state access",
                "function": event['function'],
                "event": mapped_event,
                "object": state,
                "linenumber": event['linenumber']
            })

        for child in nf_data["state_changes"][state]["child_events"]:
            for event in nf_data["state_changes"][state]["child_events"][child]["events"]:
                mapped_event = EVENT_MAP.get(event["event"], event["event"])
                timeline_of_events.append({
                    "timestamp": datetime.fromisoformat(event['timestamp']),
                    "type": "state access",
                    "function": event['function'],
                    "event": mapped_event,
                    "object": f"{state}->{child}",
                "linenumber": event['linenumber']
                })


    for function in nf_data["timemarker"]:
        for marker in nf_data["timemarker"][function]:
            timeline_of_events.append({
                "timestamp": datetime.fromisoformat(marker['timestamp']),
                "type": f"function {marker['event']}",
                "function": function,
                "event": "",
                "object": "",
                "linenumber": marker['linenumber']
            })

    timeline_of_events = sorted(timeline_of_events, key=lambda d: d['linenumber'])

    for event in timeline_of_events:
        click.echo(f"{event['timestamp']} | {event['function']} | {event['type']} | {event['object']} {event['event']}")


@click.command()
@click.option('--dump', default=False, is_flag=True)
@click.option('--nf', type=str, required=False)
@click.argument('instrumentation-json', type=click.Path(exists=True, dir_okay=False))
def main(dump, nf, instrumentation_json):
    instrumentation_data = load_json(instrumentation_json)

    if dump:
        for nf in instrumentation_data:
            if nf.startswith("__"):
                continue
            click.echo(nf)

        exit(0)

    if nf is None:
        click.echo("No function provided!")
        exit(1)

    if nf not in instrumentation_data:
        click.echo(f"NF {nf} not available in selected instrumentation_json!")
        exit(1)

    print_callstack(instrumentation_data[nf])


if __name__ == "__main__":
    main()