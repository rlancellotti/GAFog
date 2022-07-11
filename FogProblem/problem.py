import json

class Problem:
    def __init__(self, problem:json):
        self.fog = problem['fog']
        self.sensor = problem['sensor']
        self.servicechain = problem['servicechain']
        self.microservice = problem['microservice']
        if 'network' in problem:
            self.network = problem['network']
        else:
            self.network = self.fake_network(self.fog)
        self.maxrho = 0.999
        self.compute_service_params()
        self.compute_chain_params()
    
    # Creates a fake delay between the two fog nodes
    def fake_network(self, fognodes):
        rv = {}
        for f1 in fognodes:
            for f2 in fognodes:
                rv[self.get_network_key(f1, f2)] = {'delay': 0.0}
        return rv

    def get_capacity(self, f):
        if f in self.fog:
            return self.fog[f]['capacity']
        else:
            return 0
    
    def __str__(self):
        return 'services: %s' % str(list(self.microservice.keys()))
    
    # Returns the name of the two fog nodes "f1-f2"
    def get_network_key(self, f1, f2):
        return '%s-%s'%(f1, f2)

    # Searches for the delay between two fog nodes
    def get_delay(self, f1, f2):
        k = self.get_network_key(f1, f2)
        # search (f1, f2)
        if k in self.network:
            return self.network[k]
        else:
            # if not, create automatically an entry with delay=0 for f1, f1
            if f1 == f2:
                k = self.get_network_key(f1, f1) 
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
                    
    # Compute the rate and cv params
    def compute_service_params(self):
        for ms in self.microservice:
            self.microservice[ms]['rate'] = 1.0/self.microservice[ms]['meanserv']
            self.microservice[ms]['cv'] = self.microservice[ms]['stddevserv']/self.microservice[ms]['meanserv']
                
    # Returns the list of the service chain names
    def get_servicechain_list(self):
        return list(self.servicechain.keys())
        
    # Returns the list of the nodes names
    def get_fog_list(self):
        return list(self.fog.keys())

    # Returns the list of the sensors names
    def get_sensor_list(self):
        return list(self.sensor.keys())
    
    # Returns the name of the service name given a sensor name
    def get_service_for_sensor(self, s):
        sc = self.sensor[s]['servicechain']
        return self.servicechain[sc]['services'][:] 
    
    # Returns the name of the service chain for the sensor name
    def get_chain_for_sensor(self, s):
        return self.sensor[s]['servicechain']

    # Computes the lambda of the microservice and the computational power of the node
    def compute_chain_params(self):
        tot_weight = 0.0
        for sc in self.servicechain:
            lam = 0.0
            for s in self.sensor:
                if self.sensor[s]['servicechain'] == sc:
                    lam += self.sensor[s]['lambda']
            self.servicechain[sc]['lambda'] = lam
            # intialize lambda too for each microservice
            for s in self.servicechain[sc]['services']:
                self.microservice[s]['lambda'] = lam
            # initilize weight of service chain if missing
            if 'weight' not in self.servicechain[sc]:
                self.servicechain[sc]['weight'] = lam
            tot_weight += self.servicechain[sc]['weight']
        # normalize weights
        for sc in self.servicechain:
            self.servicechain[sc]['weight'] /= tot_weight # Pf or computational power of node f

    # Returns the list of the microservices names
    def get_microservice_list(self, sc=None):
        if sc is None:
            return list(self.microservice.keys())
        else:
            return self.servicechain[sc]['services']

    # Returns the params of the given microservice
    def get_microservice(self, ms):
        if ms in self.microservice:
            return self.microservice[ms]
        else:
            return None

    # Returns the params of the given node
    def get_fog(self, f):
        if f in self.fog:
            return self.fog[f]
        else:
            return None

    # Returns the number of the nodes
    def get_nfog(self):
        return len(self.fog)

    # Returns the number of the microservices
    def get_nservice(self):
        return len(self.microservice)

if __name__ == '__main__':
    with open('sample_input.json',) as f:
        data = json.load(f)
    p = Problem(data)
    print(p)

    for ms in p.get_microservice_list():
        print(ms, p.get_microservice(ms))

