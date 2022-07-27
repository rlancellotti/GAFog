import json
import sys
from math import sqrt

from ..fog_problem.problem import Problem


class Solution:

    def __init__(self, individual:list, problem:Problem):
        self.problem=problem
        self.nf=problem.get_nfog()
        self.fognames=problem.get_fog_list()
        self.nsrv=problem.get_nservice()
        self.service=problem.get_microservice_list()
        self.serviceidx=self.get_service_idx()

        # If individual is not specified or is an empty list
        if not(individual):
            individual = [None] * self.nsrv

        self.mapping = individual
        self.fog=[{}] * self.nf
        self.compute_fog_status()
        self.resptimes=None
        self.queueingtimes=None
        self.waitingtimes=None
        self.servicetimes=None
        self.deltatime=None
        self.extra_param={}

    def register_execution_time(self, deltatime):
        self.set_extra_param('deltatime', deltatime)

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

    def set_extra_param(self, param, value):
        self.extra_param[param]=value

    def get_extra_param(self, param):
        if param in self.extra_param.keys():
            return self.extra_param[param]
        else:
            return None

    def compute_fog_status(self):
        # for each fog node
        for fidx in range(self.nf):
            # get list of services for that node
            serv=self.get_service_list(fidx)
            f=self.problem.get_fog(self.fognames[fidx])
            # compute average service time for that node
            # compute stddev for that node
            # compute output inter-leaving time and stddev
            tserv=0.0
            std=0.0
            lam_tot=0.0
            for s in serv:
                # get service data
                ms=self.problem.get_microservice(s)
                # print(ms)
                # compute weights: w_i=lam_i/lam_tot
                # compute average service time: tserv=sum_i(w_i * tserv_i)
                tserv+=ms['lambda']*ms['meanserv']
                # compute stddev: std=sqrt(sum_i w_i*(sigma_i^2+mu_i^1) - mu^2)
                std+=ms['lambda']*(ms['stddevserv']**2 + ms['meanserv']**2)
                lam_tot+=ms['lambda']
                
            if lam_tot:
                tserv=tserv/lam_tot
                tserv=tserv/f['capacity']
                std=sqrt((std/lam_tot)-(tserv**2))
                std=std/f['capacity']
                # compute mu and Cov for node
                cv=std/tserv
                mu=1.0/tserv
                rho=lam_tot/mu
                twait=self.mg1_waittime(lam_tot, mu, cv)
                # print(self.fognames[fidx], tserv, std, rho, twait)
            else:
                tserv=0
                std=0
                mu=0
                cv=0
                rho=0
                twait=0
            self.fog[fidx]={
                'capacity': f['capacity'],
                'name': self.fognames[fidx],
                'tserv': tserv, 
                'stddev': std, 
                'mu': mu, 
                'cv': cv,
                'lambda': lam_tot,
                'twait': twait,
                'tresp': twait+tserv,
                'rho': rho
            }
            # print(self.fog[fidx])

    def overload_waittime(self, mu, rho):
        # if overloaded, the penalty is proportional to rho
        # this should guide the GA towards acceptable solutions
        return (rho / mu) * (self.problem.maxrho / (1 - self.problem.maxrho))

    def mm1_waittime(self, lam, mu):
        # classical M/M/1 formula
        rho=lam/mu
        if mu > lam:
            return rho / (1-rho)
        else:
            return self.overload_waittime(mu, rho)

    def mg1_waittime(self, lam, mu, cv):
        if mu==0:
            return 0
        # M/G/1 Pollaczek-Khinchin formula
        rho=lam/mu
        if mu > lam:
            rv=(1.0 / mu) * ((1.0+cv**2)/2.0)*(rho/(1.0-rho))
            # print(f'   M/G/1(tserv={1.0/mu}, cv={cv}, rho={rho})={rv}')
        else:
            rv=self.overload_waittime(mu, rho)
        return rv

    def gg1_waittime(self, lam, mu, cva, cvs):
        if mu==0:
            return 0
        # G/G/1 Allen-Cuneen formula
        rho=lam/mu
        if mu > lam:
            rv=(1.0 / mu) * ((cva**2+cvs**2)/2.0)*(rho/(1.0-rho))
            print(f'   G/G/1(tserv={1.0/mu}, cva={cva}, cvs={cvs}, rho={rho})={rv}')
        else:
            rv=self.overload_waittime(mu, rho)
        return rv

    def compute_performance(self):
        rv = {}
        # for each service chain
        for sc in self.problem.get_servicechain_list():
            prevfog=None
            tr=0.0
            twait=0.0
            tnet=0.0
            tsrv=0.0
            # for each service
            for s in self.problem.get_microservice_list(sc=sc):
                if self.mapping[self.serviceidx[s]]:
                    # get fog node id from service name
                    fidx=self.mapping[self.serviceidx[s]]
                    fname=self.fognames[fidx]
                    # add tresp for node where the service is located
                    tr+=self.fog[fidx]['twait']
                    tsrv+=self.problem.get_microservice(s)['meanserv']/self.fog[fidx]['capacity']
                    twait+=self.fog[fidx]['twait']
                    # add tnet for every node (except first)
                    if prevfog is not None:
                        tr+=self.problem.get_delay(prevfog, fname)['delay']
                        tnet+=self.problem.get_delay(prevfog, fname)['delay']
                    prevfog=fname
                else:
                    prevfog=None
            rv[sc]={'resptime': twait+tsrv+tnet, 'resptime_old': tr, 'waittime': twait, 'servicetime': tsrv, 'networktime': tnet}
        return rv

    def obj_func(self):
        tr_tot=0.0
        if not self.resptimes:
            self.resptimes=self.compute_performance()
        for sc in self.resptimes:
            # FIXME: if part of the service chain is not allocated, the obj function should reflect this in the weights!
            tr_tot+=self.resptimes[sc]['resptime']*self.problem.servicechain[sc]['weight']
        return tr_tot
    
    def dump_solution(self):
        # print('dumping solution')
        if not self.resptimes:
            self.obj_func()
        rv={'servicechain': self.resptimes, 'microservice': {}, 'sensor': {}, 'fog':{}}
        # add services in each service chain
        for sc in self.problem.get_servicechain_list():
            rv['servicechain'][sc]['services']={}
            rv['servicechain'][sc]['sensors']=[]
            for ms in self.problem.get_microservice_list(sc=sc):
                rv['servicechain'][sc]['services'][ms]=self.problem.get_microservice(ms)
            src={'startTime': 0, 'stopTime': -1, 'lambda': self.problem.servicechain[sc]['lambda']}
            rv['servicechain'][sc]['sources']=[src]
        # add sensors connected to each service chain
        for s in self.problem.get_sensor_list():
            sc=self.problem.get_chain_for_sensor(s)
            rv['servicechain'][sc]['sensors'].append(s)
        for msidx in range(self.nsrv):
            if self.mapping[msidx]:
                rv['microservice'][self.service[msidx]]=self.fognames[self.mapping[msidx]]
        for s in self.problem.sensor:
            msidx=self.serviceidx[self.problem.get_service_for_sensor(s)]
            if self.mapping[msidx]:
                rv['sensor'][s]=self.fognames[self.mapping[msidx]]
        for f in self.fog:
            rv['fog'][f['name']]={
                'rho': f['rho'], 
                'capacity': self.problem.get_fog(f['name'])['capacity'],
                'tserv': f['tserv'],
                'stddev': f['stddev'], 
                'mu': f['mu'], 
                'cv': f['cv'],
                'lambda': f['lambda'],
                'twait': f['twait'],
                }
        rv['extra']=self.extra_param
        if not self.problem.network_is_fake:
            rv['network']=self.problem.network_as_matrix()
        # print(rv)
        return rv

    def fog_from_name(self, fname):
        if not self.resptimes:
            self.obj_func()
        for f in self.fog:
            if f['name']==fname:
                return f

    def get_fog_param(self, fname, par):
        f=self.fog_from_name(fname)
        if f and par in f.keys():
            return f[par]
    
    def get_chain_param(self, scname, par):
        if not self.resptimes:
            self.obj_func()
        if scname in self.resptimes.keys() and par in self.resptimes[scname].keys():
            return self.resptimes[scname][par]

    def get_problem(self):
        return self.problem

if __name__ == "__main__":
    fin='sample/sample_input2.json' if len(sys.argv)==1 else sys.argv[1]
    print('reading from:', fin)
    with open(fin,) as f:
        prob_data = json.load(f)
    p=Problem(prob_data)
    print('problem object:', p)
    # alterante mapping [([0, 1, 1], '011'), ([1, 1, 0], '110')]
    #mappings=[([0, 0, 1, 1], '0011'), ([0, 1, 0, 1], '0101'), ([0, 1, 1, 0], '0110')]
    mappings=[([1, 1, 1], '111N')]
    for (mapping, mname) in mappings:
        fname=f'sample/sample_output_{mname}.json'
        print(f'individual object {mapping} -> {fname}')
        sol=Solution(mapping, p)
        with open(fname, 'w') as f:
            json.dump(sol.dump_solution(), f, indent=2)
            # print(json.dumps(sol.dump_solution(), indent=2))

