import json
import sys
from math import sqrt
import random

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution

class SolutionPwr(Solution):
  
    def __init__(self, chromosome, problem):
        # Structure of an individual:
        # 
        self.problem  = problem
        self.nf       = problem.get_nfog()
        self.fognames = problem.get_fog_list()
        self.nsrv     = problem.get_nservice()
        self.nfogon   = len(chromosome) - self.nsrv
        self.service  = problem.get_microservice_list()
        self.serviceidx = self.get_service_idx()
        #print(individual, self.indirect_service_mapping, self.indirect_fog_mapping)
        self.mapping    = self.get_mapping(chromosome)
        #print(self.mapping)
        self.fog        = [None] * self.nf
        self.compute_fog_status()
        self.resptimes  = None
        self.queueingtimes = None
        self.waitingtimes  = None
        self.servicetimes  = None
        self.deltatime     = None   # Used to store the execution time of the algorithm
        self.extra_param   = {}

    def get_mapping(self, individual):
        """ Returns the actual microservice mapping considering self.indirect_fog_mapping as a translation """
        mapping=[None] * self.nsrv
        current_fog=0
        for i in individual:
            if i >= self.nsrv:
                # chromosome is a fog number
                current_fog=i-self.nsrv
            else:
                mapping[i]=current_fog
        return mapping
        #indirect_service_mapping = individual[0:self.nsrv]
        #indirect_fog_mapping = individual[self.nsrv:]
        # check correctness:
        #if max(indirect_service_mapping)+1 < self.nfogon:
        #    print(f'problem will arise! services on {max(indirect_service_mapping)+1} fogs, but only {self.nfogon} on')
        #return [indirect_fog_mapping[i] for i in indirect_service_mapping]       

    def compute_fog_power(self, fidx):
        """
            Compute the power consumption of the fog (i.e. its status on or off)
            This should be called before compute_fog_performance
        """

        if self.fog[fidx] is not None and 'rho' not in self.fog[fidx].keys():
            return
        if self.fog[fidx]['rho'] == 0:
            self.fog[fidx]['power']=0
        else:
            self.fog[fidx]['power']=1
        
    def compute_fog_status(self):
        """ 
            Computes the status of all the fog nodes for a certain microservices' mapping. 
        """

        # for each fog node
        for fidx in range(self.nf):
            #print(f'compute_fog_status {fidx}')
            self.compute_fog_performance(fidx)
            self.compute_fog_power(fidx)

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
            tr = 0.0
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
                    tr += self.fog[fidx]['twait']
                    tsrv += self.problem.get_microservice(s)['meanserv'] / self.fog[fidx]['capacity']
                    twait += self.fog[fidx]['twait']
                    # add tnet for every node (except first)
                    if prevfog is not None:
                        tr   += self.problem.get_delay(prevfog, fname)['delay']
                        tnet += self.problem.get_delay(prevfog, fname)['delay']
                    prevfog = fname
                else:
                    prevfog = None
            rv[sc] = {
                'resptime': twait + tsrv + tnet,
                'resptime_old': tr,
                'waittime': twait,
                'servicetime': tsrv,
                'networktime': tnet,
            }
        return rv


    def get_pwr_obj_scale(self):
        K=100
        tot_servtime=sum(self.problem.get_microservice(item)['meanserv'] for item in self.problem.get_microservice_list())
        return K * tot_servtime

    def obj_func(self):
        """ 
            Calculates the objective function.
            Is the sum of resptime * weight for all the servicechains. 
        """
        #FIXME: must add penaties!!!
        tr_tot, pwr_tot = 0.0, 0.0
        if not self.resptimes:
            self.resptimes = self.compute_performance()
        for sc in self.resptimes:
            tr_tot += (self.resptimes[sc]['resptime'] * self.problem.servicechain[sc]['weight'])
        # FIXME: must compute power consumption for each fog!
        for fidx in range(self.nf):
            f = self.fog[fidx]
            #prevfog = None
            pwr_tot += 1 + f['rho'] if f['rho']>0 else 0
        return pwr_tot * self.get_pwr_obj_scale() + tr_tot

    def dump_solution(self):
        """ Returns a dict with all the solution params. Is used to dump the solution on a json file. """

        rv=super().dump_solution()
        for f in self.fog:
            rv['fog'][f['name']]['power'] = 1
        return rv

def normalize_individual(ind, problem: Problem):
    """ Removes unneeded elements from chromosome. Modification occurs in place """
    # remove last gene if it is a fog
    nsrv=problem.get_nservice()
    to_remove=[]
    #print(ind)
    if is_fog(ind[-1], nsrv):
        to_remove.append(len(ind)-1)
    prv_fog=True
    for i in range(1, len(ind)):
        if is_fog(ind[i], nsrv) and prv_fog:
            to_remove.append(i-1)
        prv_fog = is_fog(ind[i], nsrv)
        #print(i, ind[i], to_remove)
    print(ind, to_remove)
    for i in to_remove:
        ind.pop(i)
    return ind

def init_pwr(nfog=5, nfog_on=2, nservices=5):
    min_service=0
    max_service=nservices
    services = list(range(min_service, max_service))
    #print(services)
    #print(list(range(max_service, max_service+nfog)))
    fogs=random.sample(list(range(max_service, max_service+nfog)), nfog_on)
    #print(fogs)
    # First chromosome must always be a fog ID
    rv=services+fogs[1:]
    random.shuffle(rv)
    return fogs[0:1] + rv

def is_fog(g, nsrv):
    return g>=nsrv

def individual_to_chains(individual, problem: Problem):
    chains=[]
    size = len(individual)
    nsrv = problem.get_nservice()
    for i in range(size):
        if is_fog(individual[i], nsrv):
            ch={'fog': individual[i], 'services': []}
            chains.append(ch)
        else:
            ch['services'].append(individual[i])
    return chains

def chains_to_individual(chains):
    individual = []
    for ch in chains:
        individual += [ch['fog']]+ch['services']
    return individual

if __name__ == '__main__':
    #print(normalize_individual(init_pwr()))
    fin = "sample/sample_input2.json" if len(sys.argv) == 1 else sys.argv[1]
    print("reading from:", fin)
    with open(fin) as f:
        prob_data = json.load(f)
    p = Problem(prob_data)
    #print("problem object:", p)
    # mappings=[([0, 0, 1, 1], '0011'), ([0, 1, 0, 1], '0101'), ([0, 1, 1, 0], '0110')]
    # mappings = [([4, 0, 1, 2, 3], "111"), ([3, 4, 0, 1, 2], "111"), ([4, 0, 1, 3, 2], "110"), ([4, 0, 1, 4, 3, 2], "110")]
    mappings = [([4, 0, 1, 4, 3, 2], "110")]
    for (mapping, mname) in mappings:
        mapping = normalize_individual(mapping, p)
        print('*', mapping, individual_to_chains(mapping, p), chains_to_individual(individual_to_chains(mapping, p)))

        fname = f'sample/sample_output_{mname}.json'
        print(f'individual object {mapping} -> {fname}')
        sol = SolutionPwr(mapping, p)
        with open(fname, 'w') as f:
            json.dump(sol.dump_solution(), f, indent=2)
            # print(json.dumps(sol.dump_solution(), indent=2))

