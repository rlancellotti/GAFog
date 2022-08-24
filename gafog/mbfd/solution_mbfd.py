import string
import json
import argparse

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution


class SolutionMbfd(Solution):

    def __init__(self, problem: Problem, individual: list = [], sla=None):
        
        self.k = sla or 10 # Number multiplied by the sum of meanserv(Sm or Tc); SLA

        # If individual is not specified or is an empty list
        if not individual:
            individual = [None] * problem.get_nservice()
        
        else: # If the given list is less than the expected one adds a None at the end of individual
            for _ in range(problem.get_nservice() - len(individual)):
                individual.append(None)

        super().__init__(individual, problem)

        self.fognames = self.sort_fog()  # A name's list of the fog sorted in decreasing order by capacity
        self.compute_solution()  # Elaborates the optimal solution

    def get_initial_fog_idx(self):
            """ 
                Returns a dictonary with key=fog node not sorted and with value= position/index of the fog. 
                Used to search the standard mapping list.
            """

            rv = {}
            i = 0
            for f in self.problem.fog.keys():
                rv[f] = i
                i += 1
            return rv
      
    def get_std_map(self):
        """ 
            This function returns a list of the changed mapping.
            This should be used to pass between different algorithms' resolution because it normalizes the mapping solution
            if the fog nodes' order change.
        """
       
        ini = self.get_initial_fog_idx()
        l = []
        for fidx in self.mapping:
            if fidx is not None:
                l.append(ini[self.fog[fidx]['name']])
            else:
                l.append(None)

        return l

    def sort_fog(self):
        """It sorts fog nodes by capacity and initialize the status params."""

        return list(dict(sorted(self.problem.fog.items(), key=lambda x: x[1]['capacity'], reverse=True)).keys())

    def sort_ms(self):
        """It sorts microservices by Sm and returns a list."""
        
        return list(dict(sorted(self.problem.microservice.items(), key=lambda m: m[1]['meanserv'], reverse=True)).keys())

    def get_ms_from_chain(self, msname: string):
        """Returns the name of the service chain where is used the microservice msname."""

        for k, v in self.problem.servicechain.items():
            if msname in v['services']:  
                return k

        return None

    def compute_solution(self):
        """Computes the solution of the problem, based on the euristic algorithm of the modified best fit decreasing."""

        self.problem.begin_solution()

        # For all the microservices (sorted)
        for ms in self.sort_ms():

            # If the map for the ms is already choose
            if self.mapping[self.serviceidx[ms]] is not None:
                # Maps the idx of THIS algorithm (fog changed)
                self.mapping[self.serviceidx[ms]] = self.get_initial_fog_idx()[self.fognames[self.mapping[self.serviceidx[ms]]]]
                continue

            prev = {'fidx': 0, 'fun': None}
            s = self.get_ms_from_chain(ms)

            # For all the fog nodes, sorted too
            for fidx in range(self.nf):

                self.mapping[self.serviceidx[ms]] = fidx
                self.compute_fog_status()  # Compute the params for this solution (simulation of ms taken on the node)
                self.resptimes = self.compute_performance()  # To compute resptime (Rc)
                obj = self.obj_func()

             
                if prev['fun'] is None:
                    prev['fun'] = obj

                elif prev['fun'] > obj and self.fog[fidx]['lambda'] < self.fog[fidx]['mu']\
                     and self.fog[fidx]['tresp'] < (self.k * self.resptimes[s]['servicetime']):
                    
                    prev.update({'fidx': fidx, 'fun': obj})
                    
            self.mapping[self.serviceidx[ms]] = prev['fidx']

        self.compute_fog_status()
        self.resptimes = self.compute_performance()   
        self.set_extra_param('deltatime', self.problem.end_solution())


    def compare(self):

        sol = Solution(self.get_std_map(), self.problem)
        print(f"Solution: {sol.obj_func()}")
        print(f"Sol MBFD: {self.obj_func()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    parser.add_argument('-o', '--output', help="output file. Default output.json")
    args = parser.parse_args()
    fname = (args.file or "sample/sample_input2.json")

    with open(fname) as f:
        data = json.load(f)

    problem = Problem(data)
    sol = SolutionMbfd(problem)
    sol.compare()

    fname = "sample/" + (args.output or "output.json")
    with open(fname, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)