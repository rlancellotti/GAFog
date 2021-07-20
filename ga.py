#!/usr/bin/python3
import random
import numpy
import math
import functions
import datetime
import matplotlib.pyplot as plt

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

numGen = 500    # numero di generazioni percui continuare a fare evolevere la popolazione
numPop = 200    # numero iniziale degli individui alla prima generazione
Nfog = 6        # numero di nodi fog presenti nel database
Nsrc = 89       # numero di nodi sorgente presenti nel database
muFog = []      # lista vuota che verrà riempita con le capacità di calcolo di ogni nodo fog
lambdaSrc = []  # lista vuota che verrà riempita con i carichi di lavoro di ogni nodo sorgente
DistMatrix = []# lista vuota che verrà rimempita con una matrice delle distanze tra i nodi sorgente e quelli fog
NF = 0          #   numero di nodi da mantenere attivi
sources = []
fogs = []
delay = []
maxrho = 0.999
toolbox = base.Toolbox()


def load_individuals(creator,nsens,nfog,nf):
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
    global maxrho, muFog, lambdaSrc, Nfog, Nsrc
        
    individual = [0]*Nsrc
    for i in range(Nsrc):
        individual[i] = individual1[Nsrc + individual1[i]]
    latency = 0
    # length = len(muFog)
    length = Nfog
    lambda_fog = [0] * length
    time_fog = [0] * length
    for i in range(Nsrc):
        lambda_fog[individual[i]] += lambdaSrc[i]
    # num_nodi = funzioni.membriNodo(individual, lungh)
    for i in range(Nfog):
        if muFog[i] > lambda_fog[i]:
            time_fog[i] = 1 / (muFog[i] - lambda_fog[i])
        else:
            time_fog[i] = 1 / muFog[i] * 1 / (1 - maxrho)
    for i in range(Nsrc):
        latency += (DistMatrix[i][individual[i]] + time_fog[individual[i]])
    # valid = is_valid(individual)
    return latency,

def avg_delay():
    tot = 0
    n = 0
    for r in delay:
        tot += r[2]
        n += 1
    return (tot / n)

def normalize_delay(val):
    global delay
    tot = 0
    n = 0
    for r in delay:
        tot += r[2]
        n += 1
    avg = tot / n
    for r in delay:
        r[2] = r[2] * val / avg
        
'''Funzione che inizializza le variabili necessarie per il calcolo del fitness degli individui'''
def init_problem(lam, mu, rho, K):
    global DistMatrix,sources, fogs, delay, Nfog, NF, muFog, lambdaSrc
    #Apro la connessione al Data Base
    conne = functions.start("Tesi2.db")
    sources = functions.get_set(conne, "ID", "Source")
    fogs = functions.get_set(conne, "ID", "Fog")
    delay = functions.get_delays(conne, "Source", "Fog")
    normalize_delay(16)
    delta = avg_delay()
    DistMatrix = []
    # initialize mufog and lambdaSrc
    muFog = []
    for i in fogs:
        muFog.append(mu)
    lambdaSrc = []
    for i in sources:
        lambdaSrc.append(lam)
    y = 0
    for i in range(int(len(delay) / len(muFog))):
        mp = []
        for j in range(len(muFog)):
            mp.append(delay[j + y][2])
        DistMatrix.append(mp)
        y += len(muFog)
    # number of fog nodes to keep
    NF=(Nfog*rho*K)/(K-1)
    if NF == int(NF):
        NF=int(NF)
    else:
        NF=int(NF)+1
    print(NF)
    # close connection
    functions.stop(conne)

'''Ho modificato l'algoritmo mutUniformInt per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte '''
def mutUniformfog(individual, indpb):
    global Nsrc, Nfog, NF
    for i in range(Nsrc):
        if random.random() < indpb:
            individual[i] = random.randint(0,NF-1)
    for i in range(NF):
        if random.random() < indpb:
            sost = individual[Nsrc + i]
            while sost in individual[Nsrc:]:
                sost = random.randint(0,Nfog-1)
    return individual,
'''Ho modificato l'algoritmo cxUniform per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte'''
def cxUniformFog(ind1,ind2,indpb):
    global NF, Nsrc, Nfog
    size = min(len(ind1), len(ind2))
    for i in range(Nsrc):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    for i in range(NF):
        if random.random() < indpb:
            if ind1[Nsrc+ i] not in ind2[Nsrc:] and ind2[Nsrc+i] not in ind1[Nsrc:]:
                ind1[Nsrc+i], ind2[Nsrc+i] = ind2[Nsrc+i], ind1[Nsrc+i]
    return ind1, ind2

def init_ga():
    # Initialization
    global toolbox
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox.register("individual",load_individuals,creator.Individual,Nsrc,Nfog,NF)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cxUniformFog,indpb=0.5)
    toolbox.register("mutate", mutUniformfog, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=7)

def plot_data(x,y1,y2=None):
    # crate plots
    fig, ax1 = plt.subplots()
    line1 = ax1.plot(x, y1, "b-", label="Minimum Achieved")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Minimum", color="b")
    for tl in ax1.get_yticklabels():
        tl.set_color("b")

    if y2 != None:
        ax2 = ax1.twinx()
        line2 = ax2.plot(x, y2, "r-", label="Standard Deviation")
        ax2.set_ylabel("Deviation", color="r")
        for tl in ax2.get_yticklabels():
            tl.set_color("r")
    plt.show()


def solve_ga_Simple(cxbp,mutpb):
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
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=cxbp, mutpb=mutpb, ngen=numGen, 
                                   stats=stats, halloffame=hof, verbose=True)
    print(hof)
    print(obj_func(hof[0])[0])
    #gen=log.select("gen")
    #mins=log.select("min")
    #stds=log.select("std")
    #plot_data(gen,mins,stds)


def main():
    global sources, fogs, delay, target
    #random.seed(64)
    
    #decidere: 
    rho = 0.5
    cxbp = 0.5
    mutpb = 0.3
    K = 4
    #delta mu
    mu = 0.1

    lam = (rho * mu * Nfog) / Nsrc
    init_problem(lam,mu,rho,K)
    init_ga()
    solve_ga_Simple(cxbp,mutpb)

if __name__ == "__main__":
    main()