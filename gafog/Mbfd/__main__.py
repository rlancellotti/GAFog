import os
import json
import argparse
import time
from datetime import timedelta

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution
from .solution_mbfd import SolutionMbfd
from .mbfd import solve_problem


st = time.monotonic()  # Start time, when it begins the program

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="input file. Default sample_input2.json")
parser.add_argument("-o", "--output",help="output file. If not provided generates error")
args   = parser.parse_args()
fname  = 'sample/' + (args.file or "sample_input2.json")

with open(fname) as f:
    data = json.load(f)

sol = solve_problem(data)

if args.output:
    with open(args.output, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)
else: 
    raise TypeError('Output file not provided')

et = time.monotonic()  # end time, when its finished the execution of the program
#print(f"execution time: {timedelta(et - st)}")  
