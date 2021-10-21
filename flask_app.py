from flask import Flask, request
from ga import solve_problem

app = Flask(__name__)
# Flask API
@app.post("/api/v1.0/ga")
def post_problem():
    if request.is_json:
        data = request.get_json()
        solve_problem(data)
        return {'message': 'job submitted'}, 201
    return {'message': 'Request must be JSON'}, 415
