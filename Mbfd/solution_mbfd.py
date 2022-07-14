from math import sqrt
import sys

sys.path.append('../FogProblem')
from problem import Problem
from solution import Solution

class Solution_mbfd(Solution):

    k = 10 # Number multiplied by the sum of meanserv(Sm or Tc); SLA

    def __init__(self, problem:Problem):
        self.problem     = problem                  # The problem
        self.nf          = problem.get_nfog()       # Number of fog nodes
        self.nsrv        = problem.get_nservice()   # Number of microservices
        self.fog         = [None] * self.nf
        self.sort_fog(problem)                      # Creates a dictiorary of fog sorted by capacity
        self.sort_ms(problem)                       # List of microservices sorted by capacity(Sm or meanserv)
        self.compute_fog_status() 
        #self.compute_status()
        self.resptimes   = {}                       # TODO: used to save/update service resptimes
        self.extra_param = {}


    # It sorts fog nodes by capacity and initialize the status params
    def sort_fog(self, problem:Problem):
        self.fognames = dict(sorted(problem.fog.items(), key=lambda x: x[0][1],reverse=True))
        for node in self.fognames:
            self.fognames[node]["microservice"] = [] #[0 for _ in range(self.problem.get_nservice())] 
            self.fognames[node]["lamf"]         = 0.0
            self.fognames[node]["Sf"]           = 0.0
            self.fognames[node]["stdf"]         = 0.0
            self.fognames[node]["mu"]           = 0.0
            self.fognames[node]["cv"]           = 0.0
            self.fognames[node]["rho"]          = 0.0
            self.fognames[node]["Rf"]           = 0.0

    # It sorts microservices by Sm and returns a dictionary
    def sort_ms(self, problem:Problem):
        self.service = dict(sorted(problem.microservice.items(), key=lambda x: x[0][1], reverse=True))

    def __str__(self):
        return (str(self.fognames))

    # Return all the microservice
    def get_service_list(self):
        return self.service

    # 'returns' the solution with a list of microservices names on a certain node
    def compute_fog_status(self):

        Sf      = 0.0  
        stdf    = 0.0
        lamf    = 0.0
        Rc      = 0.0
        Sla     = 0.0
        prevfog = None

        for s in self.problem.sensor:
            self.problem.sensor[s]["resptime"]  = 0.0

        for ms in self.service.keys():
            Sf   += self.problem.microservice[ms]['lambda']*self.problem.microservice[ms]['meanserv'] 
            stdf += self.problem.microservice[ms]['lambda']*(self.problem.microservice[ms]['stddevserv']**2 + self.problem.microservice[ms]['meanserv']**2)
            lamf += self.problem.microservice[ms]['lambda']
            Sla  += self.problem.microservice[ms]['meanserv'] 

            for node in self.fognames:
    
                if lamf!=0:

                    Sf   /= lamf 
                    Sf   /= self.fognames[node]['capacity']
                    stdf  = sqrt((stdf/lamf)-(Sf**2)) 
                    stdf /= self.fognames[node]['capacity']

                    mu  = 1.0/Sf
                    cv  = stdf/Sf
                    rho = lamf/mu
                    Rf  = super().mg1_waittime(lamf, mu, cv)

                else:
                    Sf = stdf = mu = cv = rho = Rf = 0

                if ms not in [m for f in self.fognames.values() for m in f["microservice"]] \
                    and lamf<mu and Rc<(self.k*Sla): 
                 
                    for s in self.problem.sensor:
                        Rc += Rf
                        if prevfog is not None: 
                            Rc += self.problem.get_delay(prevfog, node)['delay']
                            self.problem.sensor[s]["resptime"] += Rc

                        prevfog = node
                    
                    self.fognames[node]["lamf"] = lamf
                    self.fognames[node]["Sf"]   = Sf
                    self.fognames[node]["stdf"] = stdf
                    self.fognames[node]["mu"]   = mu
                    self.fognames[node]["cv"]   = cv
                    self.fognames[node]["rho"]  = rho
                    self.fognames[node]["Rf"]   = Rf

                    self.fognames[node]["microservice"].append(ms)
    
        print(self.fognames)  
        print(self.problem.sensor)
        

    # 'returns' the solution with a list of 0/1 on a certain node
    # 1 is used when the microservice is 'taken', 0 when is not
    def compute_status(self):
        i       = 0
        Sf      = 0.0
        stdf    = 0.0
        lamf    = 0.0
        Rc      = 0.0
        Sla     = 0.0
        prevfog = None

        for s in self.problem.sensor:
            self.problem.sensor[s]["resptime"] = 0.0

        for ms in self.service.keys():
            Sf   += self.problem.microservice[ms]['lambda']*self.problem.microservice[ms]['meanserv'] 
            stdf += self.problem.microservice[ms]['lambda']*(self.problem.microservice[ms]['stddevserv']**2 + self.problem.microservice[ms]['meanserv']**2)
            lamf += self.problem.microservice[ms]['lambda']
            Sla  += self.problem.microservice[ms]['meanserv'] 

            for node in self.fognames:

                if lamf!=0:
                    Sf   /= lamf 
                    Sf   /= self.fognames[node]['capacity']
                    stdf  = sqrt((stdf/lamf)-(Sf**2)) 
                    stdf /= self.fognames[node]['capacity']

                    mu  = 1.0/Sf
                    cv  = stdf/Sf
                    rho = lamf/mu
                    Rf  = super().mg1_waittime(lamf, mu, cv)

                else:
                    Sf = stdf = mu = cv = rho = Rf = 0

                if 1 not in [f["microservice"][i] for f in self.fognames.values()] \
                    and lamf<mu and Rc<(self.k*Sla): 
                 
                    for s in self.problem.sensor:
                        Rc += Rf
                        if prevfog is not None: 
                            Rc += self.problem.get_delay(prevfog, node)['delay']
                            self.problem.sensor[s]["resptime"] += Rc

                        prevfog = node
                    
                    self.fognames[node]["lamf"] = lamf
                    self.fognames[node]["Sf"]   = Sf
                    self.fognames[node]["stdf"] = stdf
                    self.fognames[node]["mu"]   = mu
                    self.fognames[node]["cv"]   = cv
                    self.fognames[node]["rho"]  = rho
                    self.fognames[node]["Rf"]   = Rf

                    self.fognames[node]["microservice"][i] = 1
            i += 1

        #print(self.problem.sensor)
        print(self.fognames)  