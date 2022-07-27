# Benchmark microservice - charact_service

This is a simple benchmarking tool that can be used, for example, to test the service time of the GAFog algorithm (available in the ga folder of this repository).

You can set-up a simple docker enviroment as follows:

## Docker Images

Build a docker image of the services we want to use by accessing their respective directory and launch the command:

```
docker build -t CUSTOM_NAME .
```

## Docker networking

Now we are going to create a simple Docker network for convenience:

```
docker network create bench-net
```

We can now start the previously created docker images in a container and connect them to the new network with:

```
docker run --rm --net bench-net --name gafog-service -d gafog
docker run --rm --net bench-net --name bench-service -d bench
```

Where "gafog" and "bench" are the name-tags assigned to the services during the build process.

## Local Instance

It is possible to run this benchmarking microservice locally running the command:

```
python flask_app_alt.py
```

It is higly recommended to build a python virtual enviroment with the packages listed in the requirements.txt file provided in this repo.

## Accessing the APIs

To access the exposed addresses you can use your own custom container connected to the same custom network or you can acces directly the CLI of the previous containers.
The problem to use as a benchmark can be sent to the service apis with:

```
curl -X POST http://bench-service:7777/api/start -H "Content-Type:application/json -d '{"serv_location": "http://gafog-service:8080/api/v1.0/ga", "method": "post", "sync": "sync", "num_runs": 10, "json_data": "{YOUR_JSON_PROBLEM}"}'
```

where:

- method = specify the method to use aginst the tested service api (get/put/post are cuurrently supported)
- sync = specify if the expected response should be syncronous or asyncronous ("sync" / "async")
- serv_location = api address of the service to be tested (in the example gafog)
- num_runs = specify the number of iterations to repeat the test
- json_data = json payload used in put & post requests (support for different payload types is coming)

You can change the exposed ports used by the services by editing the provided Dockerfiles.

The JSON output of the benchmark service is structured as follows:

```
{
    "average": average time to solve the problem,
    "stddev": standard deviation of the times to solve the problem,
    "output": JSON of the outputs of the benchmarked service
}
```
