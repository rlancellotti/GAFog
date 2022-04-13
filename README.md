# Fog GA with Docker integration
Joint work with university of Bologna
## List of services
- ChainOptService: service to optimize the deployment of service cahins composed of multiple micro services
- CharactService: service to measure the service time of a microservice
- GraphOptService: service to create a graphic representation of a serice chain deployment (Graphviz .dot file or .svg image)

## Other relevant functions
- FogProblem general framework to define problem and solutions. Includes objective function, ability to read/dump data in JSON format
- VNSOptService: not-yet working service to implement a Variable Neighborhood Search algorithm top optimize deployment of microservices
- MM1-MG1-Omnet: GA-based algorithm to design the deployment scheme of a fog infrastructure and simulate its performance using Omnet++
