# Fog GA with Docker integration
Joint work with university of Bologna
## To execute the code locally
to run the code:
```
ga.py [-f json_input]
```

the output will be in the file spacified in json input file
## To run as service:
to run the code:
```
python flask_app.py
```

submit job with: 
```
curl -X POST -H "Content-Type: application/json" -d @sample_input2.json http://localhost:8080/api/v1.0/ga
```
## Input definition
The input is a JSON object containing the following sections:
- **fog**: fog nodes definition. Fog nodes include a 'capacity' field containing the relative capacity of the node. Capacity is a multiplier for the service throughput when deployed on that node (capacity>1 means service time is lower, capacity <1 means the service time is higher)
- **sensor**: sensor defintion. A sensor is related to a 'servicechain' and prodeces data with a rate 'lambda'
- **servicechain**: service chain definition. A servicechain contains a list called 'services' that includes (in execution order) the services belonging to that chain. A chain can contain only a sequence of services. Up to now no replication, join or fork constructs are supported. When considering the objective function, a service chain can present a 'weight' that represents the importance of its contribution in the objective function. If no weights are present, the weight is the invocation rate (lambda) of that chain. In the objetive function the weights are normalized so that their sum is 1. 
- **microservice**: microservice definition. A microservice is the component of a chain. it is characterized by a mean service time, described with key 'meanserv' and by the standard deviation of that time, with key 'stddevserv'. We model service ditribution as a gaussian distribution.
- **network**: network topology. It contains a list fo keys in the form 'Fi-Fj', with Fi and Fj being two fog nodes. For each network link we provide the network latency with the key 'delay'. If not otherwise specified, we assume Fi_Fi to have delay 0 and we assuem the links to be symmetric. Is the section is missing we assume all network delays to be negligible.

An example of the input definition can be found in the files 'sample_input.json' and 'sample_input2.json.'

Additional keywords are used to manage the delivery of the problem solution.
## Specify a solution endpoint
Solutions can be sent using:
- files
- REST endpoints
The solution endpoing is specified in the input file using the key 'response' in the input
Examples:
```
{"response": "file://sample_output2.json"}
{"response": "http://localhost:8080/api/v1.0/solution"}
```
## Relevant sources
- **problem.py**: class to define the problem structure
- **fogindividual.py**: class to wrap a solution of the genetic algorithm
- **ga.py**: core of genetic algorithm
- **flask_app.py**: wrapper to execute as flask
