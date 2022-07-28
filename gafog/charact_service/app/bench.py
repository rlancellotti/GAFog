import requests
import json
from datetime import date, datetime
import time
import statistics
from pathlib import Path

init_t = []
final_t = []

result_data = {}


def exec_test(data):
    # TODO: better error reporting
    if not verify_data(data):
        return 0

    # TODO: add use case where feedback location is "passed" to the
    #       tested service
    req_fdbck = data['req_fdbck']
    feedbck_location = data['feedbck_location']
    serv_location = data['serv_location']
    # number of times for the test to be run
    num_runs = data['num_runs']
    json_data = data['json_data']

    timing_arr = []

    for _ in range(0, num_runs):
        # Send request to micros. API location

        start = datetime.now()
        init_t.append(start)
        r = requests.post(serv_location, json=json_data)
        if not req_fdbck:
            stop = datetime.now()
            final_t.append(stop)

        if r.status_code != 201:
            return 0
        else:
            time.sleep(1)

    # start_t_file.close()
    return compute_results(num_runs)


def compute_results(runs):
    # wait if we haven't received all responses yet
    while len(init_t) != len(final_t):
        print("init len " + str(len(init_t)) + " final len " + str(len(final_t)))
        time.sleep(1)

    deltas = []

    for i in range(0, runs):
        deltas.append((final_t[i] - init_t[i]).total_seconds())

    avg = statistics.mean(deltas)
    stddev = statistics.stdev(deltas)
    output = {"output": result_data}
    output["average"] = avg
    output["stddev"] = stddev

    return output


# Check if required fields are in the input JSON data
def verify_data(data):
    if "req_fdbck" not in data:
        return 0
    if "serv_location" not in data:
        return 0
    if "json_data" not in data:
        return 0
    if "num_runs" not in data:
        return 0
    return 1


def save_execution(data):
    timestamp = datetime.now()
    final_t.append(timestamp)

    global result_data
    result_data = data


def parse_time(string_list):
    temp = []
    for elem in string_list:
        aux = elem.replace("\n", "")
        temp.append(datetime.strptime(aux, '%Y-%m-%d %H:%M:%S.%f'))

    return temp
