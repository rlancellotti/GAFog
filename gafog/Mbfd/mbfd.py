import os
import json
import argparse
import time
from datetime import timedelta

from ..FogProblem.problem import Problem
from ..FogProblem.solution import Solution
from .solution_mbfd import SolutionMbfd


# Data is a json file
def solve_problem(data:json):
    problem = Problem(data)

    return  SolutionMbfd(problem) 
    
def compare(solMBFD:SolutionMbfd):
    solGA   =  Solution(solMBFD.mapping,solMBFD.problem)
    solGA.compute_fog_status()
    if solGA.obj_func() == solMBFD.obj_func():
        return True
    
    return False



# Takes a file .json as the instance of the problem and it calls the solver 
if __name__ == "__main__":
    st  = time.monotonic() # Start time, when it begins the program

    
    parser   = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args     = parser.parse_args()
    fname    = args.file if args.file is not None else 'sample_input2.json'
    
    with open(fname,) as f:
        data = json.load(f)
    
    sol = solve_problem(data)
    
    with open('new_output.json', 'w') as f:
        json.dump(sol.dump_solution(), f, indent=2)

    
    et  = time.monotonic() # end time, when its finished the execution of the program
    print(f'execution time: {timedelta(et - st)}') # TODO: should i change it?