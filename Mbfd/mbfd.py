#!/usr/bin/python3
import sys
import json
import argparse
import time
from datetime import timedelta

sys.path.append('../')
from FogProblem.problem import Problem
from solution_mbfd import SolutionMbfd


# data is a json file
def solve_problem(data:json):
    problem  = Problem(data)
    return SolutionMbfd(problem) 
    


# takes a file .json as the instance of the problem and it calls the solver 
if __name__ == "__main__":
    st = time.monotonic()

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args = parser.parse_args()
    fname = args.file if args.file is not None else 'sample_input2.json'
    with open(fname,) as f:
        data = json.load(f)
    
    sol = solve_problem(data)
    with open('new_output.json', 'w') as f:
        json.dump(sol.dump_solution(), f, indent=2)

    et = time.monotonic()

    print(f'execution time: {timedelta(et - st)}') # TODO: i should change it?
    

