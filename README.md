# Fog GA with Docker integration

Joint work with university of Bologna

## List of services

- __charact_service__: measures the service time of a microservice
- __ga__: optimizes the deployment of service chains composed of multiple microservices
- __graph_service__: creates a graphic representation of a service chain deployment (Graphviz .dot file or .svg image)
- __problem_gen__: generates experiment to test the performance of the available algorithms

## Other relevant functions

- __fog_problem__: general framework to define problem and solutions. Includes objective function, ability to read/dump data in JSON format
- __mbfd__: modified best fit decreasing based euristic, it searches the optimal solution of microservices' deployment
- __mm1_mg1_omnet__: GA-based algorithm to design the deployment scheme of a fog infrastructure and simulate its performance using Omnet++
- __opt_service__: not-yet working service to implement a Variable Neighborhood Search algorithm top optimize deployment of microservices
- __vns__: variation of neighborhood search algorithm to minimize the object function