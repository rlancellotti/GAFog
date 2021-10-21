from flask import Flask, request, jsonify
import json
from ga import solve_problem

app = Flask(__name__)
# Flask API
# submitting jobs
@app.post("/api/v1.0/ga")
def post_problem():
    if request.is_json:
        data = request.get_json()
        solve_problem(data)
        return {'message': 'job submitted'}, 201
    return {'message': 'Request must be JSON'}, 415

# receving a solution (mainly for testing purposes)
@app.post("/api/v1.0/solution")
def post_solution():
    if request.is_json:
        print(json.dumps(request.get_json(), indent=2))
        return {'message': 'solution submitted'}, 201
    return {'message': 'Request must be JSON'}, 415

