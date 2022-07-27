import json
import argparse
import time
from datetime import timedelta

from .mbfd import solve_problem, compare


st = time.monotonic()  # Start time, when it begins the program

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="input file. Default sample_input2.json")
parser.add_argument("-o", "--output",help="output file. Default output.json")
args   = parser.parse_args()
fname  = 'sample/' + (args.file or "sample_input2.json")

with open(fname) as f:
    data = json.load(f)

sol = solve_problem(data)

fname = 'sample/' + (args.output or 'output.json')
with open(fname, "w") as f:
    json.dump(sol.dump_solution(), f, indent=2)


et = time.monotonic()  # end time, when its finished the execution of the program
print(f"execution time: {timedelta(et - st)}")  

print(compare(sol))
