from problem import Problem
from math import sqrt
import statistics
import json

class FogIndividual:

    def __init__(self, individual, problem):
        self.problem=problem
        self.nf=problem.get_nfog()
        self.fognames=problem.get_fog_list()
        self.nsrv=problem.get_nservice()
        self.service=problem.get_microservice_list()
        self.serviceidx=self.get_service_idx()
        self.mapping = individual
        self.fog=[None] * self.nf
        self.compute_fog_status()

    def get_service_idx(self):
        rv={}
        i=0
        for s in self.service:
            rv[s]=i
            i+=1
        return rv 

    def __str__(self):
        return (str(self.mapping))

    def get_service_list(self, fidx):
        rv=[]
        for s in range(self.nsrv):
            if self.mapping[s]==fidx:
                rv.append(self.service[s])
        return rv

    def compute_fog_status(self):
        # for each fog node
        for fidx in range(self.nf):
            # get list of services for that node
            serv=self.get_service_list(fidx)
            f=self.problem.get_fog(self.fognames[fidx])
            print(self.fognames[fidx], f, serv)
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
            self.fog[fidx]={
                'name': self.fognames[fidx],
                'tserv': tserv, 
                'stddev': std, 
                'mu': mu, 
                'cv': cv,
                'lambda': lam_tot,
                'tresp': self.mg1_time(lam_tot, mu, cv),
                'rho': lam_tot/mu
            }
            print(self.fog[fidx])
        
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

    def obj_func(self):
        tr_tot=0.0
        # for each service chain
        for sc in self.problem.get_servicechain_list():
            prevfog=None
            tr=0.0
            # for each service
            for s in self.problem.get_microservice_list(sc=sc):
                # get fog node id from service name
                fidx=self.mapping[self.serviceidx[s]]
                fname=self.fognames[fidx]
                # add tresp for node where the service is located
                tr+=self.fog[fidx]['tresp']
                # add tnet for every node (except first)
                print('computing netwotk delay for service', s)
                if prevfog is not None:
                    print('network delay contribution', prevfog, fname)
                    tr+=self.problem.get_delay(prevfog, fname)['delay']
                prevfog=fname
            #FIXME: consider weights for different services!
            print(tr_tot)
            tr_tot+=tr
        return tr_tot/len(self.problem.get_servicechain_list())
        
if __name__ == "__main__":
    with open('sample_input.json',) as f:
        data = json.load(f)
    print('problem objct')
    p=Problem(data)
    print(p)
    mapping=[0, 1, 1]
    print('individual objct ', mapping)
    i=FogIndividual(mapping, p)
    print('obj_func= ' + str(i.obj_func()))
    mapping=[1, 1, 0]
    print('individual objct ', mapping)
    i=FogIndividual(mapping, p)
    print('obj_func= ' + str(i.obj_func()))

