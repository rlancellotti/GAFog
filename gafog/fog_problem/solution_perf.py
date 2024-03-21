import json
import sys
from math import sqrt

from ..fog_problem.problem_perf import ProblemPerf
from ..fog_problem.solution import Solution

class SolutionPerf(Solution):
    def __init__(self, individual, problem:ProblemPerf):
        super().__init__(individual, problem)
        self.compute_fog_status()

    def __str__(self):
        return super().__str__()

    def compute_fog_performance(self, fidx):
        """ 
            Computes the status of a dingle fog node. 
            It calculates tserv, stddev, lambda, cv, mu, rho, twait and tresp.  
            All this params are then used to check if the solution is feasible or not.  
        """
        print(f'SolutionPerf.compute_fog_performance({fidx})')
        super().compute_fog_performance(fidx)

    def compute_fog_status(self):
        """ 
            Computes the status of all the fog nodes for a certain microservices' mapping. 
        """
        print('SolutionPerf.compute_fog_status()')
        super().compute_fog_status()

    def compute_performance(self):
        """ 
            Computes the performance of all the servicechains.
            It calculates resptime, waittime, servicetime and networktime.
            Returns the dict of all this params with the key that is service's name.
        """
        print('SolutionPerf.compute_performance()')
        return super().compute_performance()

    def obj_func(self):
        """ 
            Calculates the objective function.
            Is the sum of resptime * weight for all the servicechains. 
        """
        return super().obj_func()

    def dump_solution(self):
        """ Returns a dict with all the solution params. Is used to dump the solution on a json file. """
        print('call to dump_solution in SolutionPerf class')
        return super().dump_solution()

if __name__ == '__main__':
    from ..fog_problem.problem import load_problem
    fin = "sample/sample_input2.json" if len(sys.argv) == 1 else sys.argv[1]
    print("reading from:", fin)
    with open(fin) as f:
        prob_data = json.load(f)
    p = load_problem(prob_data)
    print("problem object:", p)
    # alterante mapping [([0, 1, 1], '011'), ([1, 1, 0], '110')]
    # mappings=[([0, 0, 1, 1], '0011'), ([0, 1, 0, 1], '0101'), ([0, 1, 1, 0], '0110')]
    mappings = [([1, 1, 1], "111")]
    for (mapping, mname) in mappings:
        fname = f'sample/sample_output_{mname}.json'
        print(f'individual object {mapping} -> {fname}')
        sol = p.get_solution(mapping)
        print(sol)
        with open(fname, 'w') as f:
            json.dump(sol.dump_solution(), f, indent=2)
            # print(json.dumps(sol.dump_solution(), indent=2))
