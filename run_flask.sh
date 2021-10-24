#!/bin/bash
export FLASK_APP=flask_app.py
export FLASK_ENV=development
flask run
# submit jobs with:
# curl -X POST -H 'Content-Type: application/json' -d @sample_input2.json http://localhost:8080/api/v1.0/ga