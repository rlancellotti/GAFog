import json
import sys
from math import sqrt
import random

from ..fog_problem.problem import Problem
from ..fog_problem.solution import Solution

class SolutionPwr(Solution):
  
    def __init__(self, individual, problem):
        # Structure of an individual:
        # 1) first nservices genes contains mapping of services over fog nodes
        #    fog nodes are in range 1..nfog_on
        # 2) nfog_on genes map the "on" fog nodes over the actual fog nodes.
        #    mapping elements are in range 1..nfog.
        #    each fog node can appear only once
        # super().__init__(self, individual, problem)
        self.problem  = problem
        self.nf       = problem.get_nfog()
        self.fognames = problem.get_fog_list()
        self.nsrv     = problem.get_nservice()
        self.nfogon      = len(individual) - self.nsrv
        self.service  = problem.get_microservice_list()
        self.serviceidx = self.get_service_idx()
        #print(individual, self.indirect_service_mapping, self.indirect_fog_mapping)
        self.mapping    = self.get_mapping(individual)
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

    def compute_power(self):
        pass

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
        return tr_tot

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

# TODO create genetic operators !!!

# FIXME: adapt to operator our problem
def cx_solution_pwr(ind1, ind2):
    """Executes an ordered crossover (OX) on the input
    individuals. The two individuals are modified in place. This crossover
    expects :term:`sequence` individuals of indices, the result for any other
    type of individuals is unpredictable.

    :param ind1: The first individual participating in the crossover.
    :param ind2: The second individual participating in the crossover.
    :returns: A tuple of two individuals.

    Moreover, this crossover generates holes in the input
    individuals. A hole is created when an attribute of an individual is
    between the two crossover points of the other individual. Then it rotates
    the element so that all holes are between the crossover points and fills
    them with the removed elements in order. For more details see
    [Goldberg1989]_.

    This function uses the :func:`~random.sample` function from the python base
    :mod:`random` module.

    .. [Goldberg1989] Goldberg. Genetic algorithms in search,
       optimization and machine learning. Addison Wesley, 1989
    """

    size = min(len(ind1), len(ind2))
    a, b = random.sample(range(size), 2)
    if a > b:
        a, b = b, a

    holes1, holes2 = [True] * size, [True] * size
    for i in range(size):
        if i < a or i > b:
            holes1[ind2[i]] = False
            holes2[ind1[i]] = False

    # We must keep the original values somewhere before scrambling everything
    temp1, temp2 = ind1, ind2
    k1, k2 = b + 1, b + 1
    for i in range(size):
        if not holes1[temp1[(i + b + 1) % size]]:
            ind1[k1 % size] = temp1[(i + b + 1) % size]
            k1 += 1

        if not holes2[temp2[(i + b + 1) % size]]:
            ind2[k2 % size] = temp2[(i + b + 1) % size]
            k2 += 1

    # Swap the content between a and b (included)
    for i in range(a, b + 1):
        ind1[i], ind2[i] = ind2[i], ind1[i]

    return ind1, ind2

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

def mut_del_fog(individual, indpb, problem: Problem):
    chains=individual_to_chains(individual, problem)
    ch_to_remove=[]
    for i, ch in enumerate(chains):
        if random.random() < indpb:
            ch_to_remove.append(i)
            # FIXME: move microservices to other fog ndoes
            for s in ch['services']:
                newfog = random.randint(0,len(chains))
                while newfog in ch_to_remove:
                    newfog = random.randint(0,len(chains))
                chains[i]['services'].append(s)
    for i in ch_to_remove:
        chains.pop(i)
    return individual,    

def mut_add_fog(individual, indpb, problem: Problem):
    pass
    # find list of off services
    # decide which fog to add
    # populate the fog

def mut_shuffle_pwr(individual, indpb, problem: Problem):
    """
    :param individual: Individual to be mutated.
    :param indpb: Independent probability for each attribute to be exchanged to
                  another position.
    :returns: A tuple of one individual.
    """

    size = len(individual)
    # mutate first element: it must be a fog node!
    nsrv = problem.get_nservice()
    if random.random() < indpb:
            idx_fogs=[i for i in range(size) if is_fog(individual[i], nsrv)]
            swap_indx = random.randint(1, len[idx_fogs]-1)
            individual[0], individual[swap_indx] = individual[swap_indx], individual[0]
    for i in range(1, size):
        if random.random() < indpb:
            swap_indx = random.randint(0, size - 2)
            if swap_indx >= i:
                swap_indx += 1
            individual[i], individual[swap_indx] = individual[swap_indx], individual[i]

    return normalize_individual(individual),

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

