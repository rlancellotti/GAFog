from flask import Flask, request, jsonify
import json
import requests
from .bench import exec_test, save_execution

app = Flask(__name__)
@app.post("/api/start")
def start_bench():
    if request.is_json:
        data = request.get_json()
        num = exec_test(data)
        if not num:
            print("Error")
            return {'message': 'Something happened during the test'}, 501
        return {"results": num}, 201
        # TODO: Remove all temporary files
    return {'message': 'Request must be JSON'}, 415

@app.post("/api/result")
def save_results():
    if request.is_json:
        data = request.get_json()
        save_execution(data)
        return {'message': 'Execution Time Saved'}, 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)