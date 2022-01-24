import requests
from datetime import date, datetime
import time
import json
from TestData import TestData

class Benchmark:
    def __init__(self):
        self.testData = TestData()

    def exec_test(self, data):
        # Request method check
        method = data.get("method")
        if not method:
            return "Method paramter is missing... Aborted"
        # Sync mode check
        if method != "get":
            self.synced = data.get("sync")
            if not self.synced:
                return "Syncronization parameter is missing... Aborted"
        else:
            # assume syncronous mode for get requests
            self.synced = "sync"
        # Service url to test check
        serv_location = data.get("serv_location")
        if not serv_location:
            return "Service url is missing... Aborted"
        # Number of iterations check
        num_runs = data.get("num_runs")
        if not num_runs:
            return "Num_runs parameter missing... Aborted"
        # Payload check
        if method != "get":
            json_data = data.get("json_data")
            if not json_data:
                return "Json payload missing... Aborted"
        # TODO: implement logic for different payload types

        for iter in range(0, num_runs):
            # Send requests to micros. API url
            self.testData.addIniTimestamp(datetime.now())
            if method == "get":
                r = requests.get(serv_location)
                self.sync_save(r)
            if method == "put":
                r = requests.put(serv_location, json=json_data)
                self.sync_save(r)
            if method == "post":
                r = requests.post(serv_location, json=json_data)
                self.sync_save(r)
            
            if r.status_code != 201:
                return "Service request returned " + str(r.status_code) + " status code"
            else:
                time.sleep(1)
        output = self.testData.computeRunTimes()
        return output

    def sync_save(self, request):
        if self.synced == "sync":
            self.testData.addFinTimestamp(datetime.now())
            self.testData.addResponse(json.loads(request.content.decode('utf8')))

    def save_execution(self, data):
        if self.synced == "async":
            self.testData.addFinTimestamp(datetime.now())
            if data:
                self.testData.addResponse(data)

    def clear_data(self):
        self.testData = TestData()
        self.testData.clearData()
