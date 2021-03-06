import datetime
import json
import re
from typing import Generator, Dict

import click
import pathlib

run_header_regex = re.compile(r'Open5GS daemon v.+')
log_line_regex = re.compile(r'(?P<timestamp>[0-9]{2}\/[0-9]{2} [0-9]{2}\:[0-9]{2}\:[0-9]{2}\.[0-9]{3})\: \[(?P<domain>.+?)\] (?P<level>[A-Z]+)\: (?P<message>.+?) \((?P<location>.+\:[0-9]+)\)\n')
state_data_regex = re.compile(r'\[state\]\{(?P<csv>(.*?\,)+.*?)\}(?P<version>\{.*\})?')
time_data_regex = re.compile(r'\[time\]\{(?P<csv>(.*?\,)+.*?)\}(?P<version>\{.*\})?')


def parse_open5gs_timestamp(timestamp_str: str) -> datetime.datetime:
    timestamp = datetime.datetime.strptime(timestamp_str, '%m/%d %H:%M:%S.%f')
    timestamp = timestamp.replace(year=datetime.datetime.now().year)

    return timestamp


def read_log_last_run(logfile: pathlib.Path, dump=False, run=None) -> Generator[Dict, None, None]:
    with logfile.open() as f:
        run_header_position = f.tell()
        running_position = f.tell()
        last_was_head = False
        for line in f:
            if run_header_regex.match(line):
                run_header_position = running_position
                last_was_head = True
            if dump or run is not None:
                if last_was_head and (rematch := log_line_regex.match(line)):
                    timestamp = parse_open5gs_timestamp(rematch.group('timestamp'))
                    if dump:
                        click.echo(f"Possible run: {timestamp.strftime('%Y%m%d-%H%M%S')}")
                    else:
                        diff = abs(timestamp - run)
                        if diff < datetime.timedelta(minutes=1):
                            break
                    last_was_head = False
            running_position += len(line)

        f.seek(run_header_position)
        f.readline()  # skip header line

        for line in f:
            if rematch := log_line_regex.match(line):
                values = rematch.groupdict()
                timestamp = parse_open5gs_timestamp(values['timestamp'])
                values['timestamp'] = timestamp

                yield values

            elif run_header_regex.match(line):
                break


def parse_instrumentation_messages(log_generator, instrumentation_data=None) -> Dict:
    if instrumentation_data is None:
        instrumentation_data = {'__run_timestamp': None}

    first_line = True
    for line in log_generator:
        if instrumentation_data['__run_timestamp'] is None:
            instrumentation_data['__run_timestamp'] = line['timestamp'].strftime('%Y%m%d-%H%M%S')
        elif first_line:
            run_timestamp = datetime.datetime.strptime(instrumentation_data['__run_timestamp'], '%Y%m%d-%H%M%S')
            diff = abs(line['timestamp'] - run_timestamp)
            if diff > datetime.timedelta(minutes=1):
                click.echo(f'Log data not matching run of previous analyzed logs! (prev: {run_timestamp}, this: {line["timestamp"]}, diff: {diff})')
                return instrumentation_data

        first_line = False

        if match := state_data_regex.search(line['message']):
            data = match.group('csv').split(',')
            if match.group('version') is not None:
                click.echo('Unsupported version for state data!')
                continue

            if len(data) != 4:
                continue

            nf_data = instrumentation_data.get(line['domain'], {'time': {}, 'state_changes': {}})
            obj_data = nf_data['state_changes'].get(data[0], {'events': [], 'child_events': {}})
            if data[1] == "":
                obj_data['events'].append({'event': data[2], 'timestamp': line['timestamp'].isoformat(), 'message': data[3]})
            else:
                child_events = obj_data['child_events'].get(data[1], {'events': []})
                child_events['events'].append({'event': data[2], 'timestamp': line['timestamp'].isoformat(), 'message': data[3]})

                obj_data['child_events'][data[1]] = child_events

            nf_data['state_changes'][data[0]] = obj_data
            instrumentation_data[line['domain']] = nf_data
        elif match := time_data_regex.search(line['message']):
            data = match.group('csv').split(',')
            if match.group('version') is not None:
                click.echo('Unsupported version for state data!')
                continue

            if len(data) != 2:
                continue

            nf_data = instrumentation_data.get(line['domain'], {'time': {}, 'state_changes': {}})
            timings = nf_data['time'].get(data[0], [])

            timings.append({'duration': float(data[1]), 'timestamp': line['timestamp'].isoformat()})

            nf_data['time'][data[0]] = timings
            instrumentation_data[line['domain']] = nf_data

    return instrumentation_data


@click.command()
@click.option('--dump/--no-dump', default=False)
@click.option('--run', type=str, required=False)
@click.argument('logdir', type=click.Path(exists=True, file_okay=False))
@click.argument('outdir', type=click.Path(exists=True, file_okay=False), required=False)
def main(dump, run, logdir, outdir=None):
    logdir = pathlib.Path(logdir)

    if outdir is None:
        outdir = pathlib.Path.cwd()
    else:
        outdir = pathlib.Path(outdir)

    instrumentation_data = None

    if run is not None:
        run = datetime.datetime.strptime(run, '%Y%m%d-%H%M%S')

    for logfile in logdir.glob("*.log"):
        if "mongodb" in logfile.stem:
            continue

        if dump:
            list(read_log_last_run(logfile, dump=dump))
            break

        instrumentation_data = parse_instrumentation_messages(read_log_last_run(logfile, run=run), instrumentation_data=instrumentation_data)

    if instrumentation_data is not None:
        with (outdir / f'instrumentation-data-{instrumentation_data["__run_timestamp"]}.json').open('w') as f:
            json.dump(instrumentation_data, f)
            click.echo(f'Wrote parsed state and time date to {f.name}')


if __name__ == "__main__":
    main()