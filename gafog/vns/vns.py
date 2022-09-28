import argparse
import copy
import itertools
import json
import re
import sys

import numpy as np

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution


# variation of neighborhood search algorithm for minimize opt_sol.fobj
class Vns:
    def __init__(self, problem):
        self.problem = problem
        self.solution = Solution(self.load_microservice_on_fog(), problem)
        self.c_solution = Solution(copy.deepcopy(self.solution.mapping), copy.deepcopy(problem))
        self.count = 0
        self.last_three = [None] * 3
        self.sol_counter = 0
        self.convergence = False
        self.it_convergence = 0

    def load_microservice_on_fog(self):
        individual = list()
        for i in range(self.problem.get_nservice()):
            individual.append(np.random.randint(0, self.problem.get_nfog() - 1))
        return individual

    def load_previous_microservices(self, i):
        index = re.findall(r'\d+', i)
        if int(index[1]) == 1:
            return -1
        else:
            return "MS" + str(index[0]) + "_" + str(int(index[1]) - 1)

    def find_previous_microservice(self, f1, services_on_f1, fog, latency):
        previous_microservice = [None] * len(services_on_f1)
        previous_microservice = list(map(self.load_previous_microservices, services_on_f1))
        for i in previous_microservice:
            for j in range(self.problem.get_nfog()):
                if i != -1 and i in self.c_solution.get_service_list(j):
                    fog.append(j)
                    latency.append(dict(self.problem.get_delay("F" + str(f1 + 1), "F" + str(j + 1)))['delay'])
                    break
                else:
                    if i == -1:
                        latency.append(-1.0)
                        fog.append(previous_microservice.index(i))
                        break
        return previous_microservice

    def update_solution(self):
        self.c_solution.compute_fog_status()
        self.c_solution.resptimes = None
        self.c_solution.obj_func()

    def update_optsolution(self):
        self.solution.compute_fog_status()
        self.solution.resptimes = None
        self.solution.obj_func()

    def gvns(self):
        """
        Variable Neighborhood Search function.
        """
        iter = 0
        # initialize best solution
        while iter < 2:
            if iter == 0:
                self.structure1()
                iter += 1
            else:
                self.structure2()
                iter += 1
            if self.vnd() == 1:
                iter = 0
                self.update_solution()
                self.update_optsolution()
        return self.solution

    def structure1(self):
        """
        @:param self: the object vns
        :return: swap the closest sensor with the farthest sensor
        """
        latency = []
        fog = []
        # the next while loop is used to change the random selected fog node and microservice if is the first of the
        # servicechain

        # randomly select a fog node f1
        while True:
            f1 = np.random.randint(0, (self.problem.get_nfog() - 1))
            if f1 in self.c_solution.mapping:
                break
        # the fartest sensor allocated to f1
        services_on_f1 = list(self.c_solution.get_service_list(f1))
        # Devo trovare i microservizi precedenti e valutare i delay dai fog.
        previous_microservice = self.find_previous_microservice(f1, services_on_f1, fog, latency)
        if len(latency) == 0:
            idx_microservice_f1 = 0
        else:
            idx_microservice_f1 = np.argmax(latency)
        farthest = self.c_solution.get_service_idx()[services_on_f1[idx_microservice_f1]]
        del latency[:]
        del fog[:]
        try:
            f2 = next(i for i in range(self.problem.get_nfog()) if
                      previous_microservice[idx_microservice_f1] in self.solution.get_service_list(i))
        except StopIteration:
            f2 = f1
        del previous_microservice[:]
        previous_microservice = self.find_previous_microservice(f2, list(self.c_solution.get_service_list(f2)), fog,
                                                                latency)
        if len(latency) == 0:
            idx_microservice_f2 = 0
        else:
            latency = np.ma.masked_where(np.array(latency) < 0, latency, copy=True)
            idx_microservice_f2 = np.argmin(latency)
        services_on_f2 = list(self.c_solution.get_service_list(f2))
        closest = self.c_solution.get_service_idx()[services_on_f2[idx_microservice_f2]]
        self.c_solution.mapping[farthest], self.c_solution.mapping[closest] = self.c_solution.mapping[closest], \
                                                                              self.c_solution.mapping[farthest]
        self.update_solution()

    def structure2(self):

        load = []  # vector of load of each fog node
        latency = []
        fog = []
        nfog = self.problem.get_nfog()
        for i in range(nfog):
            if self.c_solution.fog[i]['mu'] != 0:
                load.append(self.c_solution.fog[i]["lambda"] / self.c_solution.fog[i]["mu"])
            else:
                load.append(0)
        r = sum(load) / nfog
        try:
            np.max(load)
        except ValueError:
            print("\n No fog node with load")
        # the next three methods are used to random choose fog with load higher than r
        masked_load = np.ma.masked_less(load, r, copy=False)
        pos = np.random.choice(masked_load.count(), size=1)
        f1_idx = tuple(np.take((~masked_load.mask).nonzero(), pos, axis=1))
        f1_idx = f1_idx[0][0]
        services_on_f1 = list(self.c_solution.get_service_list(f1_idx))
        previous_microservice = self.find_previous_microservice(f1_idx, services_on_f1, fog, latency)
        if len(latency) == 0:
            idx_microservice_f1 = 0
        else:
            idx_microservice_f1 = np.argmax(latency)
        farthest = self.c_solution.get_service_idx()[services_on_f1[idx_microservice_f1]]
        save = self.c_solution.mapping[farthest]
        best = sys.maxsize
        idx = 0
        masked_load = np.ma.masked_greater(load, r, copy=False)
        for i in range(nfog):
            if not np.ma.is_masked(masked_load[i]):
                self.c_solution.mapping[farthest] = i
                self.update_solution()
                if self.c_solution.obj_func() <= best:
                    best = copy.copy(self.c_solution.obj_func())
                    idx = i
        self.c_solution.mapping[farthest] = idx
        self.update_solution()

    def vnd(self):
        """
        Variable Neighborhood Descent function.
        :return: 1 if the solution is improved, 0 otherwise
        """
        k = 1
        check = 0
        altered = 0
        while k < 3:
            check = 0
            if k == 1:
                microservices = self.problem.get_microservice_list()
                combinations = list(itertools.combinations(microservices, 2))
                ret = list(itertools.starmap(self.perform_swap, combinations))
                k += 1
            if k == 2:
                microservices = self.problem.get_microservice_list()
                fog = self.problem.get_fog_list()
                unique_combinations = list(itertools.product(microservices, fog))
                ret1 = list(itertools.starmap(self.perform_allocation, unique_combinations))
                k += 1
            if True in ret or True in ret1:
                k = 1
                altered = 1
        return altered

    def perform_swap(self, element, element2):
        temp = copy.deepcopy(self.c_solution.mapping)
        idx1 = self.c_solution.get_service_idx()[element]
        idx2 = self.c_solution.get_service_idx()[element2]
        self.c_solution.mapping[idx1], self.c_solution.mapping[idx2] = self.c_solution.mapping[idx2], \
                                                                       self.c_solution.mapping[idx1]
        if self.neighborhood_change():
            ret = True
        else:
            self.undo(temp)
            ret = False
        return ret

    def perform_allocation(self, element, element2):
        temp = copy.deepcopy(self.c_solution.mapping)
        idx1 = self.c_solution.get_service_idx()[element]
        fog = int(re.findall(r'\d+', element2)[0]) - 1
        self.c_solution.mapping[idx1] = fog
        if self.neighborhood_change():
            ret = True
        else:
            self.undo(temp)
            ret = False
        return ret

    def undo(self, temp):
        self.c_solution.mapping = copy.deepcopy(temp)
        self.update_solution()

    def neighborhood_change(self):
        """
        Check if the current solution is better than the best solution.
        """
        self.count += 1
        self.update_solution()
        tr_tot_c = self.c_solution.obj_func()
        tr_tot_o = self.solution.obj_func()
        if tr_tot_c < tr_tot_o:
            if self.sol_counter == 3:
                difference = (float(self.last_three[0]) - float(self.last_three[1]) - float(
                    self.last_three[2])) / float(
                    self.last_three[0]) * 100
                if difference <= 0.01 and not self.convergence:
                    self.convergence = True
                    self.it_convergence = self.count
            if not self.convergence:
                if self.sol_counter >= 3:
                    self.sol_counter = 0
                self.last_three[self.sol_counter] = float(tr_tot_c)
                self.sol_counter += 1
            self.solution.mapping = copy.deepcopy(self.c_solution.mapping)
            self.update_optsolution()
            return True


def solve_problem(prob):
    vns = Vns(prob)
    prob.begin_solution()
    sol = vns.gvns()
    prob.end_solution()
    sol.register_execution_time()
    sol.set_extra_param('conv', vns.it_convergence)
    return sol


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    parser.add_argument('-o', '--output', help="output file. Default sample_output2.json")

    args = parser.parse_args()
    fname = args.file or "sample/sample_input2.json"
    with open(fname) as f:
        data = json.load(f)
    sol = solve_problem(Problem(data))
    print(sol)

    fname = "sample/" + (args.output or "sample_output2.json")
    with open(fname, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)
