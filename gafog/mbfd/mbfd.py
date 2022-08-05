from ..fog_problem.problem import Problem
from .solution_mbfd import SolutionMbfd


# Data is a json file
def solve_problem(data: dict):
    problem = Problem(data)

    return SolutionMbfd(problem)
