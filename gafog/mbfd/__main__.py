import json
import argparse

from .mbfd import solve_problem

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help="input file. Default sample_input2.json")
parser.add_argument('-o', '--output', help="output file. Default output.json")
args = parser.parse_args()
fname = args.file or "sample/sample_input2.json"

with open(fname) as f:
    data = json.load(f)

sol = solve_problem(data)

fname = "sample/" + (args.output or "output.json")
with open(fname, "w") as f:
    json.dump(sol.dump_solution(), f, indent=2)
