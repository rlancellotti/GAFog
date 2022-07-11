#!/usr/bin/python3
from ctypes.wintypes import PINT
from http.client import FORBIDDEN
import sys
import json
import argparse

sys.path.append('../FogProblem')
from problem import Problem
from .solution_mbfd import Solution_mbfd


# data is a json file
def solve_problem(data:json):
    problem  = Problem(data)
    solution = Solution_mbfd(problem) 
    


# takes a file .json as the instance of the problem and it calls the solver 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args = parser.parse_args()
    fname = args.file if args.file is not None else 'sample_input2.json'
    with open(fname,) as f:
        data = json.load(f)
    solve_problem(data)

