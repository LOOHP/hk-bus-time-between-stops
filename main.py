import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from eta import HKEta

hketa = HKEta()
routes = list(hketa.route_list.items())


def parse_datetime(datetime_str):
    # Formats to try parsing the datetime strings
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    # If none of the formats match, raise an error indicating the issue
    raise ValueError(f"time data '{datetime_str}' does not match any supported format")


def seconds_diff(time1, time2):
    dt1 = parse_datetime(time1)
    dt2 = parse_datetime(time2)
    delta = dt2 - dt1
    return delta.total_seconds()


def run():
    key, route = random.choice(routes)
    if "stops" not in route:
        return
    stops = route["stops"]
    if len(stops) == 0:
        return
    co, stop_ids = random.choice(list(stops.items()))
    if len(stop_ids) < 2:
        return
    stop_index = random.randint(0, len(stop_ids) - 1)
    etas1 = hketa.getEtas(route_id=key, seq=stop_index, language="en")
    etas2 = hketa.getEtas(route_id=key, seq=stop_index + 1, language="en")
    if etas1 is None or etas2 is None or len(etas1) == 0 or len(etas2) == 0 or etas1[0]["eta"] is None or etas2[0]["eta"] is None:
        return
    eta_time1 = etas1[0]["eta"]
    eta_time2 = etas2[0]["eta"]
    diff = seconds_diff(eta_time1, eta_time2)
    stop_id1 = stop_ids[stop_index]
    stop_id2 = stop_ids[stop_index + 1]

    file_path = "times/" + stop_id1[0:2] + ".json"
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    data = {stop_id1: {stop_id2: diff}}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if stop_id1 in data:
                times = data[stop_id1]
                if stop_id2 in times:
                    time = times[stop_id2]
                    times[stop_id2] = (time + diff) / 2
                else:
                    times[stop_id2] = diff
            else:
                data[stop_id1] = {stop_id2: diff}
    except FileNotFoundError:
        pass
    with open(file_path, 'w') as file:
        json.dump(data, file)
    print(stop_id1 + " > " + stop_id2)


def run_repeatedly():
    try:
        while True:
            run()
    except KeyboardInterrupt:
        print("Program terminated by user")


def main():
    num_threads = 8
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_repeatedly) for _ in range(num_threads)]

        try:
            for future in as_completed(futures):
                future.result()
        except KeyboardInterrupt:
            print("Program terminated by user")
            for future in futures:
                future.cancel()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Program terminated by user")
