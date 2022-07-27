from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution
from .solution_mbfd import SolutionMbfd


# Data is a json file
def solve_problem(data:dict):
    problem = Problem(data)

    return  SolutionMbfd(problem) 
    
def compare(solMBFD:SolutionMbfd):
    sol   =  Solution(solMBFD.mapping,solMBFD.problem)
    sol.compute_fog_status()

    if sol.obj_func() == solMBFD.obj_func():
        return True
    
    return False
