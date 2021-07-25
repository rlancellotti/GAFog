import functions
import statistics

class Problem:
    # nfog  number of fog nodes
    # nsrc number of sources
    # sources list of sources
    # nf number of fog nodes to keep active
    # fogs list of fog nodes
    # mu_fog list of processing rates of fog nodes
    # lambda_src list of arrival rates of sources
    # distMatrix matrix of distances between source and fog nodes
    def __init__(self, filename, mu, delta, rho, K, maxrho):
        """Initilization 
        Parameters:
            filename (string) db filename containing the topology
            mu (float): processing rate (same for every server)
            delta (float): average delay
            rho (float): average system utilization
            K (float): SLA multiplier -> Tsla=K/mu
            K=0 -> use all fog nodes
        """
        conne = functions.start(filename)
        self.sources = functions.get_set(conne, "ID", "Source")
        self.nsrc=len(self.sources)
        self.fogs = functions.get_set(conne, "ID", "Fog")
        self.nfog=len(self.fogs)
        delays = clean_delay(functions.get_distance(conne, "Source", "Fog"))
        #print(delays)
        functions.stop(conne)
        self.maxrho=maxrho
        self.rho=rho
        self.delta=delta
        delays = normalize_delay(delays, delta)
        self.dist_matrix = []
        lam = (rho * mu * self.nfog) / self.nsrc
        self.mu_fog = []
        for i in self.fogs:
            self.mu_fog.append(mu)
        self.lambda_src = []
        for i in self.sources:
            self.lambda_src.append(lam)
        for i in range(self.nsrc):
            mp = []
            for j in range(self.nfog):
                mp.append(delays[j + i*self.nfog])
            self.dist_matrix.append(mp)
        # number of fog nodes to keep
        if K>0:
            self.nf=(self.nfog*rho*K)/(K-1)
            if self.nf == int(self.nf):
                self.nf=int(self.nf)
            else:
                self.nf=int(self.nf)+1
        else:
            self.nf=self.nfog
        #print(lam, self.nsrc, self.nfog, self.nf)

def get_avg_delay(delays):
    tot = 0
    n = 0
    for i in range(len(delays)):
        tot += delays[i]
        n += 1
    return tot / n

def normalize_delay(delays, delta):
    #print(delays)
    avg = statistics.median(delays)
    #print(avg)
    for i in range(len(delays)):
        delays[i] = delays[i] * delta / avg
    #print(statistics.median(delays))
    return delays

def clean_delay(delays):
    rv=[]
    for r in delays:
        rv.append(r[2])
    #print(rv)
    return rv