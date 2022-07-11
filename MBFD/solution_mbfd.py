from math import sqrt
import json

from problem import Problem
from solution import Solution

class Solution_mbfd(Solution):

    k = 10 # Number multiplied by the sum of Tc; SLA

    def __init__(self, problem:Problem):
        self.problem     = problem
        self.nf          = problem.get_nfog()
        self.fognames    = self.sort_fog(problem) # Dictiorary of fog sorted by capacity
        self.nsrv        = problem.get_nservice()
        self.service     = self.sort_ms(problem) # List of microservices sorted by capacity(Sm or meanserv)
        self.fog         = [None] * self.nf
        self.compute_fog_status()
        self.resptimes   = None
        self.extra_param = {}



    # It sorts fog nodes by capacity and returns a dictionary
    def sort_fog(self, problem:Problem):
        return  dict(sorted(problem.fog.items(), key=lambda x: x[0][1],reverse=True))

    # It sorts microservices by Sm and returns a dictionary
    def sort_ms(self, problem:Problem):
        return dict(sorted(problem.microservice.items(), key=lambda x: x[0][1], reverse=True))

    def __str__(self):
        return (str(self.fognames))

    # Return all the micro-service
    def get_service_list(self):
        return self.service


    def compute_fog_status(self):
        
        Sf      = 0.0
        stdf    = 0.0
        lamf    = 0.0
        Rc      = 0.0
        Sla     = 0.0
        prevfog = None

        for ms in self.service.keys():
              
            Sf   += self.problem.microservice[ms]['lambda']*self.problem.microservice[ms]['meanserv'] 
            stdf += self.problem.microservice[ms]['lambda']*(self.problem.microservice[ms]['stddevserv']**2 + self.problem.microservice[ms]['meanserv']**2)
            lamf += self.problem.microservice[ms]['lambda']
            Sla  += self.problem.microservice[ms]['meanserv'] 
            # non sicura perchè anche se non aggiorno il dict alla fine il val sommato rimane
            # TODO: controlla 


            for node in self.fognames:
                self.fognames[node]["microservice"] = []
                self.fognames[node]["lamf"]         = 0.0
                self.fognames[node]["Sf"]           = 0.0
                self.fognames[node]["stdf"]         = 0.0
                self.fognames[node]["mu"]           = 0.0
                self.fognames[node]["cv"]           = 0.0
                self.fognames[node]["rho"]          = 0.0
                self.fognames[node]["Rf"]           = 0.0
             
            
            for s in self.problem.sensor:
                self.problem.sensor[s]["resptime"]  = 0.0
   
            if lamf!=0:

                Sf   /= lamf 
                Sf   /= self.fognames[node]['capacity']
                stdf  = ((stdf/lamf)-(Sf**2))  #TODO: sqrt here
                stdf /= self.fognames[node]['capacity']

                mu  = 1.0/Sf
                cv  = stdf/Sf
                rho = lamf/mu
                Sla *= self.k
                Rf  = super().mg1_time(lamf, mu, cv)

            else:
                Sf   = 0
                stdf = 0
                mu   = 0
                cv   = 0
                rho  = 0
                Rf   = 0

            if  lamf < 1/Sf and  Rc < Sla : # TODO: change in "if ms is choosed"
                
                for s in self.problem.sensor:
                    Rc += Rf
                    if prevfog is not None: 
                        Rc += self.problem.get_delay(prevfog, node)['delay']
                        prevfog = node
                        self.problem.sensor[s]["resptime"] += Rc

                    self.fognames[node]["lamf"] = lamf
                    self.fognames[node]["Sf"]   = Sf
                    self.fognames[node]["stdf"] = stdf
                    self.fognames[node]["mu"]   = mu
                    self.fognames[node]["cv"]   = cv
                    self.fognames[node]["rho"]  = rho
                    self.fognames[node]["Rf"]   = Rf
                        
                    self.fognames[node]["microservice"].append(ms)
            else:
                lamf -= self.problem.microservice[ms]['lambda']
                Sf   -= (self.fognames[node]["Sf"] - Sf)
                stdf -= (self.fognames[node]["stdf"] - stdf)
                Sla   = (Sla/10) - self.problem.microservice[ms]['meanserv'] 

        print(self.fognames)
        print(self.service)


    def obj_func(self):
        super().obj_func()

    # Better use the one in solution.py
    def dump_solution(self):
        pass