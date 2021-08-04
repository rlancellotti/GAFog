from problem import Problem
import statistics
from mako.template import Template
from mako.runtime import Context

class FogIndividual:
    # individual1=[fog_mapping]+[source_mapping]
    # fog mapping: fog_mapping[fog]=real_fog_ID
    # source mapping: source_mapping[source]=individual_fog_ID
    colors=['red', 'teal', 'blue', 'cyan', 'magenta', 'purple']
    def __init__(self, individual, problem):
        self.problem=problem
        self.fog_mapping=[0]*problem.nf
        for i in range(problem.nf):
            self.fog_mapping[i] = individual[i+problem.nsrc]
        self.src_mapping=[0]*problem.nsrc
        for i in range(problem.nsrc):
            self.src_mapping[i] = individual[problem.nsrc + individual[i]]
        self.lambda_fog = None
        self.lambda_tot = None

    def __str__(self):
        return ("%s - %s" % (str(self.fog_mapping), str(self.src_mapping)))

    def compute_lambda_fog(self):
        if self.lambda_fog is None:
            self.lambda_fog = [0] * self.problem.nfog
            self.lambda_tot = 0
            for i in range(self.problem.nsrc):
                self.lambda_fog[self.src_mapping[i]] += self.problem.lambda_src[i]
                self.lambda_tot += self.problem.lambda_src[i]
            #self.lambda_tot=1

    def network_time(self):
        # compute for every fog node the incoming load
        self.compute_lambda_fog()
        lat_vec=[]
        time_tot = 0
        for i in range(self.problem.nsrc):    
            time_tot += self.problem.lambda_src[i] * self.problem.dist_matrix[i][self.src_mapping[i]]
            lat_vec.append(self.problem.dist_matrix[i][self.src_mapping[i]])
        return time_tot/self.lambda_tot

    def mm1_time(self, lam, mu):
        # classical M/M/1 formula
        if mu > lam:
            return 1 / (mu - lam)
        else:
            return (1 / mu) * (1 / (1 - self.problem.maxrho))

    def processing_time(self):
        time_fog = [0] * self.problem.nfog
        time_tot = 0
        # compute for every fog node the incoming load
        self.compute_lambda_fog()
        # copmute the processing time for every fog node
        for i in range(self.problem.nfog):
            time_fog[i]=self.mm1_time(self.lambda_fog[i], self.problem.mu_fog[i])
        # weighted sum of processing times
        for i in range(self.problem.nfog):
            time_tot += self.lambda_fog[i] * time_fog[i]
        return time_tot / self.lambda_tot

    def obj_func(self):
        return self.processing_time() + self.network_time()

    def create_omnet_files(self, template_prefix, out_prefix):
        # crate topology representation (.ned)
        nedtemplate=template_prefix+'.ned.mako'
        nedout=out_prefix+'.ned'
        mytemplate=Template(filename=nedtemplate)
        with open(nedout, "w") as f:
            f.write(mytemplate.render(problem=self.problem, sol=self.src_mapping, netname=out_prefix, colors=FogIndividual.colors))
        # creare simulation setup (.ini)
        initemplate=template_prefix+'.ini.mako'
        iniout=out_prefix+'.ini'
        mytemplate=Template(filename=initemplate)
        #print(mytemplate)
        with open(iniout, "w") as f:
            f.write(mytemplate.render(problem=self.problem, sol=self.src_mapping, netname=out_prefix, colors=FogIndividual.colors))
        return None
