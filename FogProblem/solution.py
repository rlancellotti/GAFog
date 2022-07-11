import string
from problem import Problem
from math import sqrt
import json

class Solution:

    def __init__(self, individual, problem:Problem):
        self.problem     = problem
        self.nf          = problem.get_nfog()
        self.fognames    = problem.get_fog_list()
        self.nsrv        = problem.get_nservice()
        self.service     = problem.get_microservice_list()
        self.serviceidx  = self.get_service_idx()
        self.mapping     = individual
        self.fog         = [None] * self.nf
        self.compute_fog_status()
        self.resptimes   = None
        self.deltatime   = None
        self.extra_param = {}

    # Returns the idx of the micro-service in the chain
    def get_service_idx(self):
        rv = {}
        i = 0
        for s in self.service: # for each micro-service
            rv[s] = i
            i += 1
        return rv 

    def __str__(self):
        return (str(self.mapping))

    def get_service_list(self, fidx):
        rv = []
        for s in range(self.nsrv): # for each micro-service
            if self.mapping[s] == fidx: # for each equal gene fidx adds the ms 
                rv.append(self.service[s])
        return rv

    # Add a new param in the class
    def set_extra_param(self, param:string, value):
        self.extra_param[param] = value

    # Return the value of the added param 
    def get_extra_param(self, param:string):
        if param in self.extra_param.keys():
            return self.extra_param[param]
        else:
            return None


    def compute_fog_status(self):
        # for each fog node
        for fidx in range(self.nf):
            # get list of services for that node
            serv = self.get_service_list(fidx)
            f = self.problem.get_fog(self.fognames[fidx])
            # compute average service time for that node
            # compute stddev for that node
            tserv = 0.0
            std = 0.0
            lam_tot = 0.0

            # for each chain
            for s in serv:
                # get micro-service data
                ms = self.problem.get_microservice(s)
                # print(ms)
                # compute weights: w_i = lam_i/lam_tot
                # compute average service time: tserv = sum_i(w_i * tserv_i)
                tserv += ms['lambda']*ms['meanserv'] 
                # compute stddev: std = sqrt(sum_i w_i*(sigma_i^2+mu_i^1) - mu^2)
                std += ms['lambda']*(ms['stddevserv']**2 + ms['meanserv']**2)
                lam_tot += ms['lambda'] 
            
            if lam_tot!=0:
                tserv = tserv/lam_tot 
                std = sqrt((std/lam_tot)-(tserv**2)) 
                tserv = tserv/f['capacity']
                std = std/f['capacity']
                # compute mu and Cov for node
                mu = 1.0/tserv
                cv = std/tserv
                rho = lam_tot/mu  # lam_tot * tserv
            else:
                tserv = 0
                std = 0
                mu = 0
                cv = 0
                rho = 0
            self.fog[fidx] = {
                'name': self.fognames[fidx],
                'tserv': tserv, 
                'stddev': std, 
                'mu': mu, 
                'cv': cv,
                'lambda': lam_tot, 
                'tresp': self.mg1_time(lam_tot, mu, cv), 
                'rho': rho
            }
            # print(self.fog[fidx])
        
    def mm1_time(self, lam, mu):
        # classical M/M/1 formula
        if mu > lam:
            return 1 / (mu - lam)
        else:
            # if overloaded, the penalty is proportional to rho
            # this should guide the GA towards acceptable solutions
            rho = lam/mu
            return (rho / mu) * (1 / (1 - self.problem.maxrho))

    # Returns, from the Pollaczek-Khinchine formula, the RESPONSE TIME
    def mg1_time(self, lam, mu, cv):
        if mu==0:
            return 0
        
        rho = lam/mu
        cv2 = cv*cv
        if mu > lam:
            return (1 / mu) * (1+((1+cv2)/2)*(rho/(1-rho)))
        else:
            # if overloaded, the penalty is proportional to rho
            # this should guide the GA towards acceptable solutions        
            return (rho / mu) * (1 / (1 - self.problem.maxrho))

    def compute_performance(self):
        rv = {}
        # for each service chain
        for sc in self.problem.get_servicechain_list():
            prevfog = None # We are at the beggining of the chain (no previous fog node)
            tr = 0.0
            
            # for each micro-service
            for s in self.problem.get_microservice_list(sc=sc):
                # get fog node id from service name
                fidx = self.mapping[self.serviceidx[s]]
                fname = self.fognames[fidx]
                # add tresp for node where the service is located
                tr += self.fog[fidx]['tresp']
                # add tnet for every node (except first)
                if prevfog is not None:
                    tr += self.problem.get_delay(prevfog, fname)['delay']
                prevfog = fname
            rv[sc] = {"resptime": tr}
        return rv


    def obj_func(self):
        tr_tot = 0.0
        if self.resptimes is None:
            self.resptimes = self.compute_performance()
        
        # Total response time for the chain 
        for sc in self.resptimes:
            tr_tot += self.resptimes[sc]['resptime']*self.problem.servicechain[sc]['weight']
        return tr_tot
    
    # Used to dump the solution in a json file
    def dump_solution(self):
        #print('dumping solution')
        if self.resptimes is None:
            self.obj_func()
        rv = {'servicechain': self.resptimes, 'microservice': {}, 'sensor': {}, 'fog':{}}
        
        # add services in each service chain
        for sc in self.problem.get_servicechain_list():
            rv['servicechain'][sc]['services'] = {}
            rv['servicechain'][sc]['sensors'] = []
            
            for ms in self.problem.get_microservice_list(sc=sc):
                rv['servicechain'][sc]['services'][ms] = self.problem.get_microservice(ms)
        
        # add sensors connected to each service chain
        for s in self.problem.get_sensor_list():
            sc = self.problem.get_chain_for_sensor(s)
            rv['servicechain'][sc]['sensors'].append(s)
        rv['servicechain'][sc]['lambda'] = self.problem.servicechain[sc]['lambda']
        #print(self.mapping)
        #print(self.obj_func())
        
        for msidx in range(self.nsrv):
            rv['microservice'][self.service[msidx]]=self.fognames[self.mapping[msidx]]
        
        for s in self.problem.sensor:
            msidx = self.serviceidx[self.problem.get_service_for_sensor(s)]
            rv['sensor'][s] = self.fognames[self.mapping[msidx]]
        
        for f in self.fog:
            rv['fog'][f['name']] = {'rho': f['rho'], 'capacity': self.problem.get_fog(f['name'])['capacity']}
        rv['extra'] = self.extra_param
        #print(rv)
        return rv
            
if __name__ == "__main__":
    with open('sample_input.json',) as f:
        data = json.load(f)
    print('problem objct')
    p = Problem(data)
    print(p)
    for mapping in [[0, 1, 1], [1, 1, 0]]:
        print('individual objct ', mapping)
        i = Solution(mapping, p)
        # print('obj_func= ' + str(i.obj_func()))
        print(json.dumps(i.dump_solution(), indent=2))

