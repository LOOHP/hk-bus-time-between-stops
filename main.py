import json
import math
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from json import JSONDecodeError

from eta import HKEta

hketa = HKEta()
routes = list(hketa.route_list.items())
file_lock = threading.Lock()


def parse_datetime(datetime_str):
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


def haversine(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


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
    stop_index = random.randint(0, len(stop_ids) - 2)

    stop_id1 = stop_ids[stop_index]
    stop_id2 = stop_ids[stop_index + 1]
    pos1 = hketa.stop_list[stop_id1]["location"]
    pos2 = hketa.stop_list[stop_id2]["location"]
    distance = haversine(pos1["lat"], pos1["lng"], pos2["lat"], pos2["lng"])
    if distance > 1.5:
        diff = distance / 0.013636
    else:
        etas1 = hketa.getEtas(route_id=key, seq=stop_index, language="en")
        etas2 = hketa.getEtas(route_id=key, seq=stop_index + 1, language="en")
        if etas1 is None or etas2 is None or len(etas1) == 0 or len(etas2) == 0 or etas1[0]["eta"] is None or etas2[0]["eta"] is None:
            return
        eta_time1 = etas1[0]["eta"]
        eta_time2 = etas2[0]["eta"]
        diff = seconds_diff(eta_time1, eta_time2)
    if diff < 0:
        return

    with file_lock:
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
                        if time < 0 or (distance > 1.5 and time < min(2.0, diff)):
                            times[stop_id2] = diff
                        else:
                            times[stop_id2] = (time + diff) / 2
                    else:
                        times[stop_id2] = diff
                else:
                    data[stop_id1] = {stop_id2: diff}
        except FileNotFoundError:
            pass
        except JSONDecodeError:
            pass
        with open(file_path, 'w') as file:
            json.dump(data, file)
    print(stop_id1 + " > " + stop_id2)


def run_repeatedly():
    while True:
        try:
            run()
        except KeyboardInterrupt:
            print("Program terminated by user")
            break
        except Exception as e:
            print(e)
            continue


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
