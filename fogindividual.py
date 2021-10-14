from problem import Problem
from math import sqrt
import statistics
import json

class FogIndividual:

    def __init__(self, individual, problem):
        self.problem=problem
        self.nf=problem.get_nfog()
        self.fog=problem.get_fog_list()
        self.nsrv=problem.get_nservice()
        self.service=problem.get_microservice_list()
        self.mapping = individual
        self.lambda_fog = None
        self.lambda_fog_component = None
        self.mu_fog = None
        self.mu_fog_component = None
        self.compute_lambda_fog()
        self.compute_mu_fog()

    def __str__(self):
        return (str(self.mapping))

    def get_service_list(self, fidx):
        rv=[]
        for s in range(self.nsrv):
            if self.mapping[s]==fidx:
                rv.append(self.service[s])
        return rv

    def compute_lambda_fog(self):
        self.lambda_fog = [0.0] * self.nf
        self.lambda_fog_component = [[0.0] * self.nsrv for f in range(self.nf)]
        microservice=self.problem.get_microservice_list()
        for sidx in range(len(microservice)):
            fidx=self.mapping[sidx]
            # get mapping of microservices
            ms=microservice[sidx]
            ms_lam=self.problem.get_microservice(ms)['lambda']
            # add microservice lambda to fog node lambda
            self.lambda_fog_component[fidx][sidx]+=ms_lam
            self.lambda_fog[fidx]+=ms_lam
        print(self.mapping)
        print(self.lambda_fog)
        print(self.lambda_fog_component)

    def compute_fog_status(self):
        self.mu_fog = [0.0] * self.nf
        self.mu_fog_component = [[0.0] * self.nsrv for f in range(self.nf)]
        # for each fog node
        for fidx in range(self.nf):
            # get list of services for that node
            serv=self.get_service_list(fidx)
            f=self.problem.get_fog(self.fog[fidx])
            print(self.fog[fidx], f, serv)
            # compute average service time for that node
            # compute stddev for that node
            tserv=0.0
            std=0.0
            lam_tot=0.0
            for s in serv:
                # get service data
                ms=self.problem.get_microservice(s)
                print(ms)
                # w_i=lam_i/lam_tot
                # tserv=sum_i(w_i * tserv_i)
                tserv+=ms['lambda']*ms['meanserv']
                # std=sqrt(sum_i w_i*(sigma_i^2+mu_i^1) - mu^2)
                std+=ms['lambda']*(ms['stddevserv']**2 + ms['meanserv']**2)
                lam_tot+=ms['lambda']
            tserv=tserv/lam_tot
            std=sqrt((std/lam_tot)-(tserv**2))
            tserv=tserv/f['capacity']
            std=std/f['capacity']
            # compute mu for node
            mu=1.0/tserv
            # computer CoV for node
            cv=std/tserv
            print(tserv, std, mu, cv)
        

    def mm1_time(self, lam, mu):
        # classical M/M/1 formula
        if mu > lam:
            return 1 / (mu - lam)
        else:
            return (1 / mu) * (1 / (1 - self.problem.maxrho))

    def mg1_time(self, lam, mu, cv):
        # M/G/1 Pollaczek-Khinchine formula
        rho=lam/mu
        cv2=cv*cv
        if mu > lam:
            return (1 / mu) * (1+((1+cv2)/2)*(rho/(1-rho)))
        else:
            return (1 / mu) * (1 / (1 - self.problem.maxrho))

    def obj_func(self, systemtype=None, cv=1):
        return None
        
if __name__ == "__main__":
    with open('sample_input.json',) as f:
        data = json.load(f)
    print('problem objct')
    p=Problem(data)
    print(p)
    mapping=[0, 1, 1]
    print('individual objct ', mapping)
    i=FogIndividual(mapping, p)
    mapping=[1, 1, 0]
    print('individual objct ', mapping)
    i=FogIndividual(mapping, p)

