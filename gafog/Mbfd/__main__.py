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
args   = parser.parse_args()
fname  = args.file or "sample/sample_input2.json"

with open(fname) as f:
    data = json.load(f)

sol = solve_problem(data)

with open("sample/new_output.json", "w") as f:
    json.dump(sol.dump_solution(), f, indent=2)


et = time.monotonic()  # end time, when its finished the execution of the program
print(f"execution time: {timedelta(et - st)}")  
