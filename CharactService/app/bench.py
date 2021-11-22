import requests
import json
from datetime import datetime
import time


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
    return 10

def save_execution(data):
    timestamp = datetime.now()
    final_t_file = open("Final_Timestamps.txt", "a")
    final_t_file.write(str(timestamp) + "\n")
    final_t_file.close()
