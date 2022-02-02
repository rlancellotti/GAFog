from flask import Flask, request, jsonify
import json
import requests
from bench import exec_test, save_execution
from bench2 import Benchmark

bench = Benchmark()
app = Flask(__name__)
@app.post("/api/start")
def start_bench():
    if request.is_json:
        bench.clear_data()
        data = request.get_json()
        num = bench.exec_test(data)
        if isinstance(num, str):
            return {'message': 'Something happened during the test', 'response': num}, 501
        return {"results": num}, 201
    return {'message': 'Request must be JSON'}, 415

@app.post("/api/result")
def save_results():
    if request.is_json:
        data = request.get_json()
        bench.save_execution(data)
        return {'message': 'Execution Time  and data Saved'}, 201
    # TODO? Support different requuest types on this side of API

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)