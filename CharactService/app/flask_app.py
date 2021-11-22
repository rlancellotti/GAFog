from flask import Flask, request, jsonify
import json
import requests
from bench import exec_test, save_execution

app = Flask(__name__)
@app.post("/api/start")
def start_bench():
    if request.is_json:
        data = request.get_json()
        num = exec_test(data)
        if num == 0:
            print("Error")
            return {'message': 'Something happened'}, 501
        return {'message': 'Benchmark completed', 'runs': num}, 201
    return {'message': 'Request must be JSON'}, 415

@app.post("/api/result")
def save_results():
    if request.is_json:
        data = request.get_json()
        save_execution(data)
        return {'message': 'Execution Time Saved'}, 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)