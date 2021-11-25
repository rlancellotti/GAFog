import requests
import json
from datetime import date, datetime
import time
import statistics
from pathlib import Path


def exec_test(data):
    #testFile = open("./samples/sample_input2.json", )
    #data = json.load(testFile)
    feedbck_location = data['feedbck_location']
    serv_location = data['serv_location']
    json_data = data['json_data']

    if serv_location == '' or json_data == '' or feedbck_location == '':
        return 0
    
    # Add/update response field in JSON obj
    json_data['response'] = feedbck_location
    start_t_file = open("Init_Timestamps.txt", "a")

    for iter in range(0, 10):
        # Send request to micros. API
        start = datetime.now()
        #r = requests.post("http://gafog:8080/api/v1.0/ga", json=data)
        r = requests.post(serv_location, json=json_data)
        if r.status_code != 201:
            return 0
        else:
            start_t_file.write(str(start) + "\n")
            time.sleep(2)

    start_t_file.close()
    return compute_results()

def debug():
    nani = open("nani.txt", "a")
    nani.write("Sofar so good\n")
    nani.close()


def compute_results():
    # Open timestamp files
    
    start_file = open("Init_Timestamps.txt", "r")
    start_times = start_file.readlines()
    end_file = open("Final_Timestamps.txt", "r")
    end_times = end_file.readlines()
    results = open("Results.json", "r")
    json_data = json.load(results)
    debug()
    # To datetime format
    start_times = parse_time(start_times)
    end_times = parse_time(end_times)
    debug()
    deltas = []
    for i in range(0,10):
        deltas.append((end_times[i] - start_times[i]).total_seconds())
    debug()
    avg = statistics.mean(deltas)
    stddev = statistics.stdev(deltas)
    output = {"output": json_data}
    output["average"] = avg
    output["stddev"] = stddev
    debug()
    return output


def save_execution(data):
    timestamp = datetime.now()
    final_t_file = open("Final_Timestamps.txt", "a")
    final_t_file.write(str(timestamp) + "\n")
    final_t_file.close()
    computed_file = Path("./Results.json")
    if not computed_file.exists():
        computed_file = open("Results.json", "w")
        computed_file.write(json.dumps(data))
        computed_file.close()

def parse_time(string_list):
    temp = []
    for elem in string_list:
        aux = elem.replace("\n", "")
        temp.append(datetime.strptime(aux, '%Y-%m-%d %H:%M:%S.%f'))
    
    return temp