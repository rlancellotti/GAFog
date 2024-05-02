import json
import sys
from math import sqrt

from ..fog_problem.problem import Problem


class Solution:
  
    def __init__(self, individual, problem):
        self.problem  = problem
        self.nf       = problem.get_nfog()
        self.fognames = problem.get_fog_list()
        self.nsrv     = problem.get_nservice()
        self.service  = problem.get_microservice_list()
        self.serviceidx = self.get_service_idx()
        self.mapping    = individual
        self.fog        = [None] * self.nf
        self.resptimes  = None
        self.queueingtimes = None
        self.waitingtimes  = None
        self.servicetimes  = None
        self.deltatime     = None   # Used to store the execution time of the algorithm
        self.extra_param   = {}
        self.compute_fog_status()

    def register_execution_time(self, deltatime=None):
        """ Saves the execution time. If it isn't passed it find it in the problem params. """
        if deltatime:
            self.set_extra_param('deltatime', deltatime)
        else:
            self.set_extra_param('deltatime', self.problem.get_solution_time())

    def get_service_idx(self):
        """ Returns a mapped dict where the key is the name of the service and the value is an index. """
        return {s : n for (n, s) in enumerate(self.service)}

    def __str__(self):
        return str(self.mapping)

    def get_service_list(self, fidx):
        """ Returns a list of all the microservices allocated in the fog node of the given index. """
        return [self.service[n] for (n, s) in enumerate(self.mapping) if s==fidx]

    def set_extra_param(self, param, value):
        """ Sets a new param in an object Solution. """
        self.extra_param[param] = value

    def get_extra_param(self, param):
        """ Get the value of the given param if it exist. """
        if param in self.extra_param.keys():
            return self.extra_param[param]

    def compute_fog_performance(self, fidx):
        """ 
            Computes the status of a single fog node. 
            It calculates tserv, stddev, lambda, cv, mu, rho, twait and tresp.  
            All this params are then used to check if the solution is feasible or not.  
        """
        #print(f'copmute_fog_performance {fidx}')
        if self.fog[fidx] is not None and 'rho' in self.fog[fidx].keys():
            return
        #print(self.mapping)
        # get list of services for that node
        serv = self.get_service_list(fidx)
        #print(fidx, serv)
        f    = self.problem.get_fog(self.fognames[fidx])
        # compute average service time for that node
        # compute stddev for that node
        # compute output inter-leaving time and stddev
        tserv = 0.0
        std   = 0.0
        lam_tot = 0.0
        #print(serv)
        for s in serv:
            # get service data
            ms = self.problem.get_microservice(s)
            #print(s, ms)
            # compute weights: w_i=lam_i/lam_tot
            # compute average service time: tserv=sum_i(w_i * tserv_i)
            tserv += ms['lambda'] * ms['meanserv']
            #print(f'{s}: lambda: {ms["lambda"]}, ts: {ms["meanserv"]}')
            # compute stddev: std=sqrt(sum_i w_i*(sigma_i^2+mu_i^1) - mu^2)
            std += ms['lambda'] * (ms['stddevserv']**2 + ms['meanserv']**2)
            lam_tot += ms['lambda']
        if lam_tot != 0:
            #tserv_old=tserv
            tserv = tserv / lam_tot
            std = sqrt((std/lam_tot) - (tserv**2))
            tserv = tserv / f['capacity']
            std = std / f['capacity']
            #print(f'tserv={tserv_old}/({lam_tot}*{f["capacity"]})={tserv}\n')
            # compute mu and Cov for node
            cv = std / tserv
            mu = 1.0 / tserv
            rho   = lam_tot * tserv
            twait = self.mg1_waittime(lam_tot, mu, cv)
            # print(f'twait(lam={lam_tot}, mu={mu}, cv={cv})={twait}')
            # print(self.fognames[fidx], tserv, std, rho, twait)
        else:
            tserv, std, mu, cv, rho, twait = 0, 0, 0, 0, 0, 0
        self.fog[fidx] = {
            'capacity': f['capacity'],
            'name': self.fognames[fidx],
            'tserv': tserv, 
            'stddev': std, 
            'mu': mu, 
            'cv': cv,
            'lambda': lam_tot,
            'twait': twait,
            'tresp': twait + tserv,
            'rho': rho
        }
        # print(self.fog[fidx])

    def compute_fog_status(self):
        """ 
            Computes the status of all the fog nodes for a certain microservices' mapping. 
        """
        # for each fog node
        for fidx in range(self.nf):
            self.compute_fog_performance(fidx)

    def is_rho_overload(self, rho):
        return rho>=1.0

    def is_node_overload(self, fidx):
        self.compute_fog_performance(fidx)
        return self.is_rho_overload(self.fog[fidx]['rho'])

    def get_overload_penalty(self):
        penalty=0.0
        for f in self.fog:
            if f is not None and 'rho' in f.keys() and f['rho']>=1:
                penalty += f['rho']
        return penalty

    def get_SLA_penalty(self):
        penalty=0.0
        if not self.resptimes:
            self.resptimes = self.compute_performance()
        for sc in self.resptimes:
            if self.resptimes[sc]['resptime'] > self.problem.servicechain[sc]['sla']:
                penalty += self.resptimes[sc]['resptime']/self.problem.servicechain[sc]['meanserv']
        return penalty

    def get_penalty(self):
        return self.get_overload_penalty() * self.nf + self.get_SLA_penalty() * len(self.problem.get_get_servicechain_list())

    def overload_waittime(self, mu, rho):
        # if overloaded, the penalty is proportional to rho
        # this should guide the GA towards acceptable solutions
        return (rho / mu) * (self.problem.maxrho / (1 - self.problem.maxrho))

    def mm1_waittime(self, lam, mu):
        # classical M/M/1 formula
        rho = lam / mu
        if self.is_rho_overload(rho):
            return self.overload_waittime(mu, rho)
        else:
            return rho / (1 - rho)

    def mg1_waittime(self, lam, mu, cv):
        """ 
            Calculates and returns the result of the Pollaczek-Khinchin formula.
            Used to find tresp.
        """

        if mu == 0:
            return 0
        # M/G/1 Pollaczek-Khinchin formula
        rho = lam / mu
        if self.is_rho_overload(rho):
            rv = self.overload_waittime(mu, rho)
            #print('overload detected!')
        else:
            rv = (1.0 / mu) * ((1.0 + cv**2) / 2.0) * (rho / (1.0 - rho))
        return rv

    def gg1_waittime(self, lam, mu, cva, cvs):
        if mu == 0:
            return 0
        # G/G/1 Allen-Cuneen formula
        rho = lam / mu
        if mu > lam:
            rv = (1.0 / mu) * ((cva**2 + cvs**2) / 2.0) * (rho / (1.0 - rho))
            #print(f'G/G/1(tserv={1.0/mu}, cva={cva}, cvs={cvs}, rho={rho})={rv}')
        else:
            rv = self.overload_waittime(mu, rho)
        return rv

    def compute_performance(self):
        """ 
            Computes the performance of all the servicechains.
            It calculates resptime, waittime, servicetime and networktime.
            Returns the dict of all this params with the key that is service's name.
        """
        rv = {}
        # for each service chain
        for sc in self.problem.get_servicechain_list():
            prevfog = None
            twait = 0.0
            tnet  = 0.0
            tsrv  = 0.0
            # for each service
            for s in self.problem.get_microservice_list(sc=sc):
                if self.mapping[self.serviceidx[s]] is not None:
                    # get fog node id from service name
                    fidx  = self.mapping[self.serviceidx[s]]
                    fname = self.fognames[fidx]
                    # add tresp for node where the service is located
                    tsrv += self.problem.get_microservice(s)['meanserv'] / self.fog[fidx]['capacity']
                    twait += self.fog[fidx]['twait']
                    # add tnet for every node (except first)
                    if prevfog is not None:
                        tnet += self.problem.get_delay(prevfog, fname)['delay']
                    prevfog = fname
                else:
                    prevfog = None
            rv[sc] = {
                'resptime': twait + tsrv + tnet,
                'waittime': twait,
                'servicetime': tsrv,
                'networktime': tnet,
                'sla': self.problem.servicechain[sc]['sla']
            }
        return rv

    def obj_func(self):
        """ 
            Calculates the objective function.
            Is the sum of resptime * weight for all the servicechains. 
        """
        tr_tot = 0.0
        if not self.resptimes:
            self.resptimes = self.compute_performance()
        for sc in self.resptimes:
            tr_tot += (self.resptimes[sc]['resptime'] * self.problem.servicechain[sc]['weight'])
        penalty=self.get_penalty()
        return tr_tot + penalty

    def dump_solution(self):
        """ Returns a dict with all the solution params. Is used to dump the solution on a json file. """
        # print('dumping solution')

        self.set_extra_param('obj_func', self.obj_func())
        rv = {'servicechain': self.resptimes, 'microservice': {}, 'sensor': {}, 'fog':{}}

        # add services in each service chain
        for sc in self.problem.get_servicechain_list():
            rv['servicechain'][sc]['services'] = {}
            rv['servicechain'][sc]['sensors']  = []
            for ms in self.problem.get_microservice_list(sc=sc):
                rv['servicechain'][sc]['services'][ms] = self.problem.get_microservice(ms)
            src = {'startTime': 0, 'stopTime': -1, 'lambda': self.problem.servicechain[sc]['lambda']}
            rv['servicechain'][sc]['sources'] = [src]

        # add sensors connected to each service chain
        for s in self.problem.get_sensor_list():
            sc = self.problem.get_chain_for_sensor(s)
            rv['servicechain'][sc]['sensors'].append(s)

        for msidx in range(self.nsrv):
            if self.mapping[msidx] is not None:
                rv['microservice'][self.service[msidx]] = self.fognames[self.mapping[msidx]]
                
        for s in self.problem.sensor:
            msidx = self.serviceidx[self.problem.get_service_for_sensor(s)]
            if self.mapping[msidx] is not None:
                rv['sensor'][s] = self.fognames[self.mapping[msidx]]

        for f in self.fog:
            rv['fog'][f['name']] = {
                'rho': f['rho'], 
                'capacity': self.problem.get_fog(f['name'])['capacity'],
                'tserv': f['tserv'],
                'stddev': f['stddev'], 
                'mu': f['mu'], 
                'cv': f['cv'],
                'lambda': f['lambda'],
                'twait': f['twait'],
            }

        rv['extra'] = self.extra_param
        if not self.problem.network_is_fake:
            rv['network'] = self.problem.network_as_matrix()
        # print(rv)
        return rv

    def fog_from_name(self, fname):
        """ 
            From a given fog node's name it returns the status.
            It calcutes the status' fog if was not.
        """
        if not self.resptimes:
            self.obj_func()
        for f in self.fog:
            if f['name'] == fname:
                return f

    def get_fog_param(self, fname, par):
        """ From a given fog name and a param it returns the value. """

        f = self.fog_from_name(fname)
        if f and par in f.keys():
            return f[par]

    def get_chain_param(self, scname, par):
        """  
            From a given servicechain's name it returns the performance.
            It calcutes the performance' servicechain if was not.
        """
        
        if not self.resptimes:
            self.obj_func()
        if scname in self.resptimes.keys() and par in self.resptimes[scname].keys():
            return self.resptimes[scname][par]

    def get_problem(self):
        return self.problem

if __name__ == '__main__':
    fin = "sample/sample_input2.json" if len(sys.argv) == 1 else sys.argv[1]
    print("reading from:", fin)
    with open(fin) as f:
        prob_data = json.load(f)
    p = Problem(prob_data)
    print("problem object:", p)
    # alterante mapping [([0, 1, 1], '011'), ([1, 1, 0], '110')]
    # mappings=[([0, 0, 1, 1], '0011'), ([0, 1, 0, 1], '0101'), ([0, 1, 1, 0], '0110')]
    mappings = [([1, 1, 1], "111")]
    for (mapping, mname) in mappings:
        fname = f'sample/sample_output_{mname}.json'
        print(f'individual object {mapping} -> {fname}')
        sol = Solution(mapping, p)
        with open(fname, 'w') as f:
            json.dump(sol.dump_solution(), f, indent=2)
            # print(json.dumps(sol.dump_solution(), indent=2))
