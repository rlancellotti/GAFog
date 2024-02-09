#!/usr/bin/env python3
#from mako.template import Template
import argparse
import json
from diagrams import Diagram, Cluster, Edge
from diagrams.alibabacloud.compute import ElasticComputeService as Fog
from diagrams.alibabacloud.iot import IotLinkWan as Sensor
from diagrams.alibabacloud.compute import WebAppService as Service
import os

def begin_of_chain(data, sc):
    return list(data['servicechain'][sc]['services'].keys())[0]

fontsize="30.0"

def make_diagram(data, outfile):
    graph_attr = {
        "fontsize": fontsize
    }
    with Diagram('', show=True, filename=outfile, direction="LR", graph_attr=graph_attr):
        with Cluster('Sensors', graph_attr=graph_attr):
            sens={}
            for s in data['sensor'].keys():
                sens[s]=Sensor(s, fontsize=fontsize)
        with Cluster('Micro-services', graph_attr=graph_attr):
            svc={}
            for sc in data['servicechain'].keys():
                with Cluster(f'Service chain {sc}', graph_attr=graph_attr):
                    prev_s=None
                    for s in data['servicechain'][sc]['services'].keys():
                        svc[s]=Service(s, fontsize=fontsize)
                        # Service Chain links
                        if prev_s is not None:
                            svc[prev_s] >> Edge(color='blue', style='solid') >>svc[s]
                        prev_s=s
        # Data fow sensor -> service chains
        #print(svc)
        for sc in data['servicechain']:
            for s in data['servicechain'][sc]['sensors']:
                #print(s, begin_of_chain(data, sc))
                sens[s] >> Edge(color='darkgreen', style='solid') >> svc[begin_of_chain(data, sc)]
        with Cluster('Fog nodes', graph_attr=graph_attr):
            fog={}
            for f in data['fog'].keys():
                fog[f]=Fog(f, fontsize=fontsize)
        # mapping of services to fog nodes
        for s in data['microservice']:
            svc[s] >> Edge(style="dashed") >> fog[data['microservice'][s]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='output file. Default graph.png')
    parser.add_argument('-f', '--file', help='input file. Default use sample_output.json')
    args   = parser.parse_args()
    fdata  = args.file or "sample/sample_output_111.json"
    with open(fdata, 'r') as f:
        data  = json.load(f)
    fout = args.output or "sample/graph"
    make_diagram(data, fout)
