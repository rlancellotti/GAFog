# Fog GA with Docker integration
Joint work with university of Bologna
## To execute the code locally
- to run the code:
        ga.py [-f json_input]
- the output will be in the file spacified in json input file
## To run service:
- to run the code:
        run_flask.sh
- submit job with: 
        curl -X POST -H 'Content-Type: application/json' -d @sample_input2.json http://localhost:5000/api/v1.0/ga
## Relevant sources
- **problem.py**: class to define the problem structure
- **fogindividual.py**: class to wrap a solution of the genetic algorithm
- **ga.py**: core of genetic algorithm
- **flask_app.py**: wrapper to execute as flask
