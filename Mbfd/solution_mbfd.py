import string
import sys
import json
import argparse
from math import sqrt

from ..FogProblem.problem import Problem
from ..FogProblem.solution import Solution


class SolutionMbfd(Solution):

    k = 10 # Number multiplied by the sum of meanserv(Sm or Tc); SLA
 
    def __init__(self, problem:Problem, individual:list=[]):
        
        self.problem     = problem                   # The problem
        self.nf          = problem.get_nfog()        # Number of fog nodes
        self.fognames    = self.sort_fog(problem)    # A name's list of the fog sorted in decreasing order by capacity
        self.nsrv        = problem.get_nservice()    # Number of services
        self.service     = self.sort_ms(problem)     # List of microservices sorted by capacity(Sm or meanserv)
        self.serviceidx  = self.get_service_idx()    # Dict of indexed services

        # If individual is not specified or is an empty list
        if not(individual):
            self.mapping = [None] * self.nsrv   # Is represented by all None
        else:
            self.mapping = individual           # Is represented by the already taken and the not taken

        self.fog         = [{}] * self.nf    # Dict of information about the single fog nodes
        self.resptimes   = None              # Information about the resptimes of the service chains
        self.extra_param = {}                

        self.fog_initialize()                   # Init for self.fog
        self.compute_solution()                 # Elaborates the optimal solution        


    def sort_fog(self, problem:Problem):
        """ It sorts fog nodes by capacity and initialize the status params. """

        return list(dict(sorted(problem.fog.items(), key=lambda x: x[0][1],reverse=True)).keys())
        

    def fog_initialize(self):
        """
            Initialization of fog nodes, adds the first empty values.
            If the solution is calculated for a list of nodes already in the solution we simply
            initialize the list of microservices with the names already in the solution.
        """

        for fidx in range(self.nf):
            self.fog[fidx] =  {
                'name': self.fognames[fidx],
                'capacity': self.problem.get_fog(self.fognames[fidx])['capacity'],
                'microservices': self.get_service_list(fidx), 
                'twait':  0.0,
                'tserv':  0.0, 
                'stddev': 0.0, 
                'mu':     0.0, 
                'cv':     0.0,
                'lambda': 0.0,
                'tresp':  0.0,
                'rho':    0.0, }


    def sort_ms(self, problem:Problem):
        """ It sorts microservices by Sm and returns a list. """

        return list(dict(sorted(problem.microservice.items(), key=lambda x: x[0][1], reverse=True)).keys())


    def get_ms_from_chain(self, msname:string):
        """ Returns the name of the service chain where is used the microservice msname. """ 

        for k, c in self.problem.servicechain.items():
            if msname in c['services']:  
                return k
        
        return None


    def compute_solution(self):
        """ Calculates the solution with a list of microservices names on a certain node. """

        tserv   = 0.0  # Avg. service time for the fog node (Sf)
        std     = 0.0  # Standard deviation of tserv 
        lam_tot = 0.0  # Incoming request rate to fog node
        Sm      = 0.0  # Avg. service time for the microservice (Sm or Tc), used for the calculation of the SLA 
        twait   = 0.0  # Avg. response time for the fog node (Rf)
        X_func  = None # Obj_func's value for the first iteration  

        # For all the microservices (already sorted)
        for ms in self.service :
            
            # If the microservice is already in the solution/on a fog node skips to the next iteration
            if not self.mapping[self.get_service_idx()[ms]] is None:  
                continue

            tserv   += self.problem.microservice[ms]['lambda']*self.problem.microservice[ms]['meanserv'] 
            std     += self.problem.microservice[ms]['lambda']*(self.problem.microservice[ms]['stddevserv']**2 + self.problem.microservice[ms]['meanserv']**2)
            lam_tot += self.problem.microservice[ms]['lambda']
            Sm      += self.problem.microservice[ms]['meanserv'] 

            # For all the fog nodes, sorted too
            for fidx in range(self.nf):
                f = self.problem.get_fog(self.fognames[fidx]) # Information of the fog node

                if lam_tot!=0:

                    tserv /= lam_tot
                    tserv /= f['capacity']
                    std    = sqrt((std/lam_tot)-(tserv**2)) 
                    std   /= f['capacity']

                    mu     = 1.0/tserv
                    cv     = std/tserv
                    rho    = lam_tot/mu
                    twait  = self.mg1_waittime(lam_tot, mu, cv)

                else:
                    tserv = std = mu = cv = rho = twait = 0

                self.resptimes = self.compute_performance() # To compute resptime (Rc)
                X_current      = self.obj_func() # current value of obj_func

                # Decision for the optimal solution, decides if a microservice is allocated on the node
                if ms not in self.fog[0]['microservices'] and lam_tot<mu \
                   and self.resptimes[self.get_ms_from_chain(ms)]['resptime']<(self.k*Sm): 

                    self.fog[fidx].update({
                        'tserv':  tserv, 
                        'stddev': std, 
                        'mu':     mu, 
                        'cv':     cv,
                        'lambda': lam_tot,
                        'twait':  twait,
                        'tresp':  twait + tserv,
                        'rho':    rho,    }) 

                    self.fog[fidx]['microservices'].append(ms)      # Tracks the taken microservices 
                    self.mapping[self.get_service_idx()[ms]] = fidx # Maps that the microservice ms entered in the solution
              
                X_func = X_current # The old value of obj_func (X_func) replaced by the new value
                


if __name__ == "__main__":
    parser   = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args     = parser.parse_args()
    fname    = args.file if args.file is not None else 'sample_input2.json'
    
    with open(fname,) as f:
        data = json.load(f)
    
    problem  = Problem(data)
    sol      = SolutionMbfd(problem, [None, None, None]) 