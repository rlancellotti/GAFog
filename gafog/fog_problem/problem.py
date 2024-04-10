import json
import time

#from ..fog_problem.problProblem.dict()em_pwr import ProblemPwr

def load_problem(problem_dct: dict):
    from ..fog_problem.problem_perf import ProblemPerf
    from ..fog_problem.problem_pwr import ProblemPwr
    print(problem_dct.keys())
    if 'type' in problem_dct.keys(): print(problem_dct['type'])
    if 'type' in problem_dct.keys() and problem_dct['type'] == 'performance':
        return ProblemPerf(problem_dct)
    if 'type' in problem_dct.keys() and problem_dct['type'] == 'power':
        return ProblemPwr(problem_dct)
    return ProblemPerf(problem_dct)

class Problem:
    def __init__(self, problem_dct: dict):
        self.response = problem_dct['response'] if 'response' in problem_dct.keys() else None
        self.fog = problem_dct['fog']
        self.sensor = problem_dct['sensor']
        self.servicechain = problem_dct['servicechain']
        self.microservice = problem_dct['microservice']
        self.handle_network(problem_dct)
            
        self.maxrho = 0.999
        self.compute_service_params()
        self.compute_chain_params()

    def handle_network(self, problem_dct: dict):
        if 'network' in problem_dct:
            self.network_is_fake = False
            self.network = problem_dct['network']
        else:
            self.network_is_fake = True
            self.network = self.fake_network(self.fog)

    def dump_problem(self):
        """ Returns a dict of the problem's values. """
        rv = {
            'fog': self.fog,
            'sensor': self.sensor,
            'servicechain': self.servicechain,
            'microservice': self.microservice
            }
        if not self.network_is_fake:
            rv['network'] = self.network
        if self.response is not None:
            rv['response'] = self.response
        return rv

    def get_solution(self, chromosome):
        from ..fog_problem.solution import Solution as solution_module
        return solution_module(chromosome, self)

    def fake_network(self, fognodes):
        """ 
            If network is not 'enabled'/is not in the json file, it returns a fake one
            where the delay is always 0.
        """
        rv = {}
        for f1 in fognodes:
            for f2 in fognodes:
                rv[self.get_network_key(f1, f2)] = {'delay': 0.0}
        return rv

    def get_capacity(self, f):
        """ Returns the capacity of the given fog node. """
        if f in self.fog:
            return self.fog[f]['capacity']
        else:
            return 0

    def __str__(self):
        return 'services: %s' % str(list(self.microservice.keys()))

    def get_network_key(self, f1, f2):
        """ 
            Given two nodes it 'cast' them in the right string. 
            Is used as a key to get the value of the delay between these nodes.
        """
        return '%s-%s'%(f1, f2)

    def get_delay(self, f1, f2):
        """ Returns the delay between two given nodes. """
        k = self.get_network_key(f1, f2)
        # search (f1, f2)
        if k in self.network:
            return self.network[k]
        else:
            # if not, create automatically an entry with delay=0 for f1, f1
            if f1 == f2:
                k  = self.get_network_key(f1, f1)
                rv = {'delay': 0.0}
                self.network[k] = rv
                return rv
            else:
                # otherwise look for reverse mapping
                k = self.get_network_key(f2, f1)
                if k in self.network:
                    self.network[self.get_network_key(f1, f2)] = self.network[k]
                    return self.network[k]
                else:
                    # distance not found!
                    return None

    def compute_service_params(self):
        """ Computes rate and cv for all the microservices in the list. """
        for ms in self.microservice:
            self.microservice[ms]['rate'] = 1.0 / self.microservice[ms]['meanserv']
            self.microservice[ms]['cv']   = self.microservice[ms]['stddevserv'] / self.microservice[ms]['meanserv']

    def get_servicechain_list(self):
        """ Returns the list of the service chain's names. """
        return list(self.servicechain.keys())

    def get_fog_list(self):
        """ Returns the list of fog nodes' names. """
        return list(self.fog.keys())

    def get_sensor_list(self):
        """ Returns the list of the sensor's names. """
        return list(self.sensor.keys())

    def get_service_for_sensor(self, s):
        """ Returns the list of microservice on a certain servicechain given the name of the sensor. """
        sc = self.sensor[s]['servicechain']
        return self.servicechain[sc]['services'][0]

    def get_chain_for_sensor(self, s):
        """ Returns the name of the servicechain on a given sensor. """
        return self.sensor[s]['servicechain']

    def compute_chain_params(self):
        """ 
            Computes the params of all the servicechain. 
            It calculates lambda and weight.    
        """
        tot_weight = 0.0
        for sc in self.servicechain:
            lam = 0.0
            for s in self.sensor:
                if self.sensor[s]['servicechain'] == sc:
                    lam += self.sensor[s]['lambda']
            self.servicechain[sc]['lambda'] = lam
            # intialize also lambda for each microservice
            # lambda_i=lambda_i-1*(1-p_exit_i-1)
            lam_i = lam
            pexit = 0.0
            for s in self.servicechain[sc]['services']:
                self.microservice[s]['lambda'] = lam_i
                lam_i = lam_i*(1-pexit)
                pexit = self.microservice[s]['exitprobability'] if 'exitprobability' in self.microservice[s].keys() else 0.0
            # initilize weight of service chain if missing
            if 'weight' not in self.servicechain[sc]:
                self.servicechain[sc]['weight'] = lam
            tot_weight += self.servicechain[sc]['weight']
        # normalize weights
        for sc in self.servicechain:
            self.servicechain[sc]['weight'] /= tot_weight

    def get_microservice_list(self, sc=None):
        """ 
            Returns the microservices' on a given servicechain.
            If none is specified it returns all the microservices. 
        """
        if not sc:
            return list(self.microservice.keys())
        else:
            return self.servicechain[sc]['services']

    def get_microservice(self, ms):
        """ 
            Returns all the params in the dict of the given microservice. 
            If ms doesn't exists then it returns None. 
        """
        if ms in self.microservice:
            return self.microservice[ms]

    def get_fog(self, f):
        """ 
            Returns all the params in the dict of the given fog node. 
            If f doesn't exists then it returns None. 
        """
        if f in self.fog:
            return self.fog[f]

    def get_nfog(self):
        """ Returns the number of the fog nodes. """
        return len(self.fog)

    def get_nservice(self):
        """ Returns the total number of microservices. """
        return len(self.microservice)

    def network_as_matrix(self):
        """ Returns a matrix where every f1 have a list of all the f2 is linked to. """
        rv = []
        for f1 in self.get_fog_list():
            l = []
            for f2 in self.get_fog_list():
                l.append(self.get_delay(f1, f2)['delay'])
            rv.append(l)
        return rv

    def get_response_url(self):
        return self.response

    def begin_solution(self):
        """ Starts time, when a solver is 'activated'. Is used to calculate the execution time. """
        self.start_time = time.perf_counter_ns()

    def end_solution(self):
        """ Ends the time, when the solver is stopped. Is used to calculate the execution time. """
        self.end_time = time.perf_counter_ns()
        self.solution_time = (self.end_time - self.start_time) / 1e9
        return self.solution_time

    def get_solution_time(self):
        """ Returns the execution time if it was calculated. """
        try:
            return self.solution_time
        except AttributeError:
            return -1.0
    
    def get_problem_type(self):
        return self.__class__.__name__
    
if __name__ == '__main__':
    with open('sample/sample_input2.json') as f:
        data = json.load(f)
    
    p = Problem(data)
    print(p)
    
    for ms in p.get_microservice_list():
        print(ms, p.get_microservice(ms))