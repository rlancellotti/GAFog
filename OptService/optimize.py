#!/usr/bin/python3
import sys
import json
import argparse
import requests
from enum import Enum

sys.path.append('../')
from FogProblem.problem import Problem
from FogProblem.solution import Solution
import GA.ga as gamod

class Algorithms(Enum):
    GA='GA'
    VNS='VNS'
    MBFD='MBFD'
    AMPL='AMPL'

available_algorithms=[Algorithms.GA]

def algorithm_by_name(algo):
    for a in available_algorithms:
        if algo == a.name:
            return a
    return None

def write_solution(fout, sol):
    with open(fout, "w+") as f:
        json.dump(sol.dump_solution(), f, indent=2)


def solve_problem(problem: Problem, algo):
    match algo:
        case Algorithms.GA:
            return gamod.solve_problem(problem)

def send_response(sol: Solution, default_url=None):
    resp=sol.get_problem().get_response_url()
    if resp is None:
        if default_url is None:
            return
        else:
            resp=default_url
    if resp.startswith('file://'):
        write_solution(resp.lstrip('file://'), sol)
    else:
        # use requests package to send results
        requests.post(data['response'], json=sol.dump_solution())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    parser.add_argument('-a', '--algo', help='algorithm. Available: GA (default), MBFD, VNS, AMPL')
    args = parser.parse_args()
    fname=args.file if args.file is not None else 'sample_input2.json'
    algoname=args.algo if (args.algo is not None) else 'GA'
    algo=algorithm_by_name(algoname)
    if algo is None:
        print(f'algorithm {algoname} is not valid')
        sys.exit()
    with open(fname,) as f:
        data = json.load(f)
    sol=solve_problem(Problem(data), algo)
    print(sol)
    if sol:
        send_response(sol)