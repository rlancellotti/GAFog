# Fog GA with Docker integration

Joint work with university of Bologna

## List of services

- __ga__: optimizes the deployment of service chains composed of multiple microservices
- __charact_service__: measures the service time of a microservice
- __graph_opt_service__: creates a graphic representation of a service chain deployment (Graphviz .dot file or .svg image)

## Other relevant functions

- __fog_problem__: general framework to define problem and solutions. Includes objective function, ability to read/dump data in JSON format
- __opt_service__: not-yet working service to implement a Variable Neighborhood Search algorithm top optimize deployment of microservices
- __mm1_mg1_omnet__: GA-based algorithm to design the deployment scheme of a fog infrastructure and simulate its performance using Omnet++
- __mbfd__: modified-best-fit-decreasinfìg based euristic, it searches the optimal solution of microservices' deployment
