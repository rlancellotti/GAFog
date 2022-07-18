from math import sqrt
import sys
import json
import argparse

sys.path.append('../FogProblem')
from problem import Problem
from solution import Solution

class Solution_mbfd(Solution):

    k = 10 # Number multiplied by the sum of meanserv(Sm or Tc); SLA

    # TODO: chiamare super() e poi le funzioni specifiche implementate 
    def __init__(self, problem:Problem, individual=[]):
        
        self.problem        = problem
        self.nf             = problem.get_nfog()
        self.fognames       = problem.get_fog_list()
        self.nsrv           = problem.get_nservice()
        self.service        = problem.get_microservice_list()
        self.serviceidx     = self.get_service_idx()
        if not(individual):
            self.mapping = [None] * self.nsrv
        else:
            self.mapping = individual

        self.fog            = [{}] * self.nf
        self.resptimes      = None
        self.queueingtimes  = None
        self.waitingtimes   = None
        self.servicetimes   = None
        self.deltatime      = None
        self.extra_param    = {}

        self.sort_fog(problem)                          # A name's list of the fog in decreasing order by capacity
        self.fog_initialize()                           # Init for self.fog
        self.sort_ms(problem)                           # List of microservices sorted by capacity(Sm or meanserv)
        self.compute_fog_status() 


    # It sorts fog nodes by capacity and initialize the status params
    def sort_fog(self, problem:Problem):
        self.fognames = list(dict(sorted(problem.fog.items(), key=lambda x: x[0][1],reverse=True)).keys())
        
        
    def fog_initialize(self):
        for fidx in range(self.nf):
            self.fog[fidx]= {
                'name': self.fognames[fidx],
                'capacity': self.problem.get_fog(self.fognames[fidx])['capacity'],
                'microservices': [],
                'twait': 0.0,
                }

    # It sorts microservices by Sm and returns a dictionary
    def sort_ms(self, problem:Problem):
        self.service = dict(sorted(problem.microservice.items(), key=lambda x: x[0][1], reverse=True))

    def get_ms_from_chain(self, msname='MS1_1'):
        for k, c in self.problem.servicechain.items():
            if msname in c['services']:
                return k
        return None


    # 'returns' the solution with a list of microservices names on a certain node
    def compute_fog_status(self):

        tserv       = 0.0  
        std         = 0.0
        lam_tot     = 0.0
        Sla         = 0.0
        twait       = 0.0
        X_func      = None # Its the obj_func for the first iteration  

        for ms in self.service :
            if not self.mapping[self.get_service_idx()[ms]] is None: 
                continue
            
            sc = self.get_ms_from_chain(ms)

            tserv += self.problem.microservice[ms]['lambda']*self.problem.microservice[ms]['meanserv'] 
            std += self.problem.microservice[ms]['lambda']*(self.problem.microservice[ms]['stddevserv']**2 + self.problem.microservice[ms]['meanserv']**2)
            lam_tot += self.problem.microservice[ms]['lambda']
            Sla  += self.problem.microservice[ms]['meanserv'] 

            for fidx in range(self.nf):
                f = self.problem.get_fog(self.fognames[fidx])
                if lam_tot!=0:

                    tserv /= lam_tot
                    tserv /= f['capacity']
                    std  = sqrt((std/lam_tot)-(tserv**2)) 
                    std /= f['capacity']

                    mu  = 1.0/tserv
                    cv  = std/tserv
                    rho = lam_tot/mu
                    twait  = super().mg1_waittime(lam_tot, mu, cv)

                else:
                    tserv = std = mu = cv = rho = twait = 0

                self.resptimes = super().compute_performance() # To compute resptime (Rc)
                if ms not in [m for f in self.fog for m in f["microservices"]] \
                    and lam_tot<mu and self.resptimes[sc]['resptime']<(self.k*Sla) \
                    and (X_func==None or X_func>self.obj_func()):

                    

                    self.fog[fidx].update({
                        'tserv': tserv, 
                        'stddev': std, 
                        'mu': mu, 
                        'cv': cv,
                        'lambda': lam_tot,
                        'twait': twait,
                        'tresp': twait + tserv,
                        'rho': rho,
                        }) 

                    self.fog[fidx]['microservices'].append(ms)
                    self.mapping[self.get_service_idx()[ms]] = fidx

        print(self.fog)
        print(self.resptimes)
        print(self.mapping)
        



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args = parser.parse_args()
    fname = args.file if args.file is not None else 'sample_input2.json'
    with open(fname,) as f:
        data = json.load(f)
    problem  = Problem(data)
    solution = Solution_mbfd(problem, [0, None, None]) 