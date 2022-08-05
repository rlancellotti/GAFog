import string
import json
import argparse

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution


class SolutionMbfd(Solution):

    k = 10  # Number multiplied by the sum of meanserv(Sm or Tc); SLA

    def __init__(self, problem: Problem, individual: list = []):

        # If individual is not specified or is an empty list
        if not individual:
            individual = [None] * problem.get_nservice()

        super().__init__(individual, problem)

        self.fog_initialize()  # Init for self.fog params
        self.fognames = self.sort_fog(problem)  # A name's list of the fog sorted in decreasing order by capacity
        self.service = self.sort_ms(problem)  # List of microservices sorted by capacity(Sm or meanserv)
        self.compute_solution()  # Elaborates the optimal solution


# TODO: aggiungere soluzione da indice sorted a indice std

    def sort_fog(self, problem: Problem):
        """It sorts fog nodes by capacity and initialize the status params."""

        return list(dict(sorted(problem.fog.items(), key=lambda x: x[0][1], reverse=True)).keys())

    def fog_initialize(self):
        """
        Initialization of fog nodes, adds the first empty values.
        If the solution is calculated for a list of nodes already in the solution we simply
        initialize the list of microservices with the names already in the solution.
        """

        for fidx in range(self.nf):
            self.fog[fidx].update(
                {
                'name': self.fognames[fidx],
                'capacity': self.problem.get_fog(self.fognames[fidx])['capacity'],
                'microservices': self.get_service_list(fidx), 
                }
            )


    def sort_ms(self, problem: Problem):
        """It sorts microservices by Sm and returns a list."""

        return list(dict(sorted(problem.microservice.items(), key=lambda x: x[0][1], reverse=True)).keys())

    def get_ms_from_chain(self, msname: string):
        """Returns the name of the service chain where is used the microservice msname."""

        for k, c in self.problem.servicechain.items():
            if msname in c['services']:  
                return k

        return None

    def compute_solution(self):
        """Computes the solution of the problem, based on the euristic algorithm of the modified best fit decreasing."""
        self.problem.begin_solution()

        Sm = 0.0  # Avg. service time for the microservice (Sm or Tc), used for the calculation of the SLA

        # For all the microservices (already sorted)
        for ms in self.service:

            # If the microservice is already in the solution/on a fog node, it skips to the next iteration
            if not self.mapping[self.get_service_idx()[ms]] is None:
                continue

            Sm += self.problem.microservice[ms]['meanserv'] 

            # For all the fog nodes, sorted too
            for fidx in range(self.nf):

                self.mapping[self.serviceidx[ms]] = fidx
                self.compute_fog_status()  # Compute the params for this solution (= if the node is taken on fidx)

                self.resptimes = self.compute_performance()  # To compute resptime (Rc)

                # Decision for the optimal solution, decides if a microservice is allocated on the node
                if self.fog[fidx]['lambda'] < self.fog[fidx]['mu'] \
                   and self.resptimes[self.get_ms_from_chain(ms)]['resptime']<(self.k*Sm): 

                    self.mapping[self.serviceidx[ms]] = fidx  # Maps that the microservice ms entered in the solution
                    break
                    # The opt solution is choosen and it doesnt need to search for better allocation

                else:
                    # This was not the best solution so we have to repeat this search with the remaining nodes
                    self.mapping[self.serviceidx[ms]] = None
        self.set_extra_param('execution time', self.problem.end_solution())

    def compare(self):
        """Not finished yet, It should compare the obj_func of two different solution."""
        # TODO: it should be done with ga algorithm?

        sol = Solution(self.mapping, self.problem)
        print(f'Solution\'s obj func: {sol.obj_func()}')
        print(f'SolutionMbfd\'s obj func: {self.obj_func()}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    parser.add_argument('-o', '--output', help="output file. Default output.json")
    args = parser.parse_args()
    fname = 'sample/' + (args.file or "sample_input2.json")

    with open(fname) as f:
        data = json.load(f)

    problem = Problem(data)
    sol = SolutionMbfd(problem, [None, None, None])

    fname = "sample/" + (args.output or "output.json")
    with open(fname, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)
