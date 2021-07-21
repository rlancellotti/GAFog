#!/usr/bin/python3
import random
import numpy
import math
import functions
import datetime
import matplotlib.pyplot as plt
from collections import namedtuple

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

class Problem:
    # nfog  number of fog nodes
    # nsrc number of sources
    # sources list of sources
    # nf number of fog nodes to keep active
    # fogs list of fog nodes
    # mu_fog list of processing rates of fog nodes
    # lambda_src list of arrival rates of sources
    # distMatrix matrix of distances between source and fog nodes
    def __init__(self, filename, mu, delta, rho, K):
        """Initilization 
        Parameters:
            filename (string) db filename containing the topology
            mu (float): processing rate (same for every server)
            delta (float): average delay
            rho (float): average system utilization
            K (float): SLA multiplier -> Tsla=K/mu
        """
        conne = functions.start(filename)
        self.sources = functions.get_set(conne, "ID", "Source")
        self.nsrc=len(problem.sources)
        self.fogs = functions.get_set(conne, "ID", "Fog")
        self.nfog=len(problem.fogs)
        delays = functions.get_delays(conne, "Source", "Fog")
        functions.stop(conne)
        normalize_delay(delays, delta)
        self.dist_matrix = []
        self.fogs
        lam = (rho * mu * self.nfog) / self.nsrc
        self.mufog = []
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
        self.nf=(self.nfog*rho*K)/(K-1)
        if self.nf == int(self.nf):
            self.nf=int(self.nf)
        else:
            self.nf=int(self.nf)+1
        print(self.nf)


def init_problem(mu, delta, rho, K):
    problem=Problem(None, None, None, None, None, None, None, None)
    #global DistMatrix,sources, fogs, delay, Nfog, NF, muFog, lambdaSrc
    #Apro la connessione al Data Base
    # initialize mufog and lambdaSrc
    return problem



 

numGen = 500    # numero di generazioni percui continuare a fare evolevere la popolazione
numPop = 200    # numero iniziale degli individui alla prima generazione
maxrho = 0.999



def load_individuals(creator, nsens, nfog, nf):
    individual = list()
    for i in range(nsens):
        individual.append(random.randint(0,nf-1))
    nodi = random.sample(range(nfog),nf)
    #print(nodi)
    for i in range(len(nodi)):
        individual.append(nodi[i])
    #print(individual)
    return creator(individual)

def obj_func(individual1):
    global maxrho, problem
    # individual1=[fog_mapping]+[source_mapping]
    # fog mapping: fog_mapping[fog]=real_fog_ID
    # source mapping: source_mapping[source]=individual_fog_ID
    individual = [0]*problem.nsrc
    for i in range(problem.nsrc):
        individual[i] = individual1[problem.nsrc + individual1[i]]
    latency = 0
    # length = len(muFog)
    length = problem.nfog
    lambda_fog = [0] * length
    time_fog = [0] * length
    for i in range(problem.nsrc):
        lambda_fog[individual[i]] += problem.lambdaSrc[i]
    # num_nodi = funzioni.membriNodo(individual, lungh)
    for i in range(problem.nsrc):
        if problem.muFog[i] > lambda_fog[i]:
            time_fog[i] = 1 / (problem.muFog[i] - lambda_fog[i])
        else:
            time_fog[i] = 1 / problem.muFog[i] * 1 / (1 - maxrho)
    for i in range(problem.nsrc):
        latency += (problem.distMatrix[i][individual[i]] + time_fog[individual[i]])
    # valid = is_valid(individual)
    return latency,

def normalize_delay(delays, newavg):
    tot = 0
    n = 0
    for r in delays:
        tot += r[2]
        n += 1
    avg = tot / n
    for r in delays:
        r[2] = r[2] * newavg / avg
        


def mutUniformfog(individual, indpb):
    global problem
    for i in range(problem.nsrc):
        if random.random() < indpb:
            individual[i] = random.randint(0,problem.nf-1)
    for i in range(problem.nf):
        if random.random() < indpb:
            sost = individual[problem.nsrc + i]
            while sost in individual[problem.nsrc:]:
                sost = random.randint(0,problem.nfog-1)
    return individual,

'''Ho modificato l'algoritmo cxUniform per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte'''
def cxUniformFog(ind1,ind2,indpb):
    global problem
    #size = min(len(ind1), len(ind2))
    for i in range(problem.nsrc):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    for i in range(problem.nf):
        if random.random() < indpb:
            if ind1[problem.nsrc+ i] not in ind2[problem.nsrc:] and ind2[problem.nsrc+i] not in ind1[problem.nsrc:]:
                ind1[problem.nsrc+i], ind2[problem.nsrc+i] = ind2[problem.nsrc+i], ind1[problem.nsrc+i]
    return ind1, ind2

def init_ga():
    # Initialization
    toolbox = base.Toolbox()
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox.register("individual",load_individuals,creator.Individual,Nsrc,Nfog,NF)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cxUniformFog,indpb=0.5)
    toolbox.register("mutate", mutUniformfog, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=7)
    return toolbox

def plot_data(x,y1,y2=None):
    # crate plots
    fig, ax1 = plt.subplots()
    ax1.plot(x, y1, "b-", label="Minimum Achieved")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Minimum", color="b")
    for tl in ax1.get_yticklabels():
        tl.set_color("b")

    if y2 != None:
        ax2 = ax1.twinx()
        ax2.plot(x, y2, "r-", label="Standard Deviation")
        ax2.set_ylabel("Deviation", color="r")
        for tl in ax2.get_yticklabels():
            tl.set_color("r")
    plt.show()


def solve_ga_simple(toolbox, cxbp,mutpb):
    # GA solver
    global numPop, numGen
    pop = toolbox.population(n=numPop)
    # dico di salvare in hof il migliore (1) individuo mai esistito durante l'evoluzione
    hof = tools.HallOfFame(1)
    # inizializzo un Logbook che provvederà a salvare tutte le statistiche richieste https://deap.readthedocs.io/en/master/tutorials/basic/part3.html
    log = tools.Logbook()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    # Change verbose parameter to see population evolution
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=cxbp, mutpb=mutpb, ngen=numGen, 
                                   stats=stats, halloffame=hof, verbose=False)
    print(hof)
    print(obj_func(hof[0])[0])
    #gen=log.select("gen")
    #mins=log.select("min")
    #stds=log.select("std")
    #plot_data(gen,mins,stds)


if __name__ == "__main__":
    #random.seed(64)
    #decidere: 
    rho = 0.5
    cxbp = 0.5
    mutpb = 0.3
    K = 4
    #delta mu
    mu = 0.1
    delta = 0.1
    problem = Problem('Tesi2.db', mu, delta, rho, K)
    toolbox=init_ga()
    solve_ga_simple(toolbox, cxbp, mutpb)

