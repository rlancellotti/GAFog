import functions

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
        delays = functions.get_delays(conne, "Source", "Fog")
        self.maxrho=maxrho
        functions.stop(conne)
        delays = normalize_delay(delays, delta)
        self.dist_matrix = []
        lam = (rho * mu * self.nfog) / self.nsrc
        self.mu_fog = []
        for i in self.fogs:
            self.mu_fog.append(mu)
        self.lambda_src = []
        for i in self.sources:
            self.lambda_src.append(lam)
        y = 0
        for i in range(int(len(delays) / len(self.mu_fog))):
            mp = []
            for j in range(len(self.mu_fog)):
                mp.append(delays[j + y][2])
            self.dist_matrix.append(mp)
            y += len(self.mu_fog)
        # number of fog nodes to keep
        if K>0:
            self.nf=(self.nfog*rho*K)/(K-1)
            if self.nf == int(self.nf):
                self.nf=int(self.nf)
            else:
                self.nf=int(self.nf)+1
        else:
            self.nf=self.nfog
        print(lam, self.nsrc, self.nfog, self.nf)
        #print(self.nf)

def get_avg_delay(delays):
    tot = 0
    n = 0
    for r in delays:
        tot += r[2]
        n += 1
    return tot / n

def normalize_delay(delays, newavg):
    #print(delays)
    avg = get_avg_delay(delays)
    print(avg)
    for r in delays:
        r[2] = r[2] * newavg / avg
    print(get_avg_delay(delays))
    return delays