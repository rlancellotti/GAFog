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
fogN = 6        # numero di nodi fog presenti nel database
sorN = 89       # numero di nodi sorgente presenti nel database
muFog = []      # lista vuota che verrà riempita con le capacità di calcolo di ogni nodo fog
lambdaSrc = []  # lista vuota che verrà riempita con i carichi di lavoro di ogni nodo sorgente
DistMatrix = []# lista vuota che verrà rimempita con una matrice delle distanze tra i nodi sorgente e quelli fog
NF = 0          #   numero di nodi da mantenere attivi
sources = []
fogs = []
rit = []
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
    global maxrho, muFog, lambdaSrc, fogN, sorN
        
    individual = [0]*sorN
    for i in range(sorN):
        individual[i] = individual1[sorN + individual1[i]]
    
    latency = 0
    # length = len(muFog)
    length = fogN
    lambda_fog = [0] * length
    time_fog = [0] * length
    for i in range(sorN):
        lambda_fog[individual[i]] += lambdaSrc[i]
    # num_nodi = funzioni.membriNodo(individual, lungh)
    for i in range(fogN):
        if muFog[i] > lambda_fog[i]:
            time_fog[i] = 1 / (muFog[i] - lambda_fog[i])
        else:
            time_fog[i] = 1 / muFog[i] * 1 / (1 - maxrho)
    for i in range(sorN):
        latency += (DistMatrix[i][individual[i]] + time_fog[individual[i]])
    # valid = is_valid(individual)
    return latency,

def avg_rit():
    tot = 0
    n = 0
    for r in rit:
        tot += r[2]
        n += 1
    return (tot / n)

def normalize_rit(val):
    global rit
    tot = 0
    n = 0
    for r in rit:
        tot += r[2]
        n += 1
    avg = tot / n
    for r in rit:
        r[2] = r[2] * val / avg
'''Funzione che inizializza le variabili necessarie per il calcolo del fitness degli individui'''
def init_problem(lam, mu, rho, K):
    global DistMatrix,sources, fogs, rit, fogN, NF
    #Apro la connessione al Data Base
    conne = functions.start()
    sources = functions.get_set(conne, "ID", "Source")
    fogs = functions.get_set(conne, "ID", "Fog")
    rit = functions.get_ritardi(conne, "Source", "Fog")

    normalize_rit(16)
    delta = avg_rit()

    DistMatrix = []
    '''Assegno ad ogni nodo fog una capacità di calcolo 333 e a ogni nodo sogente
       un lavoro da svolgere di un job/s'''
    global muFog, lambdaSrc
    muFog = []
    for i in fogs:
        muFog.append(mu)
    lambdaSrc = []
    for i in sources:
        lambdaSrc.append(lam)

    ''' creo la matrice delle distanze utilizzando i ritardi ottenuti con get_ritardi'''
    y = 0
    for i in range(int(len(rit) / len(muFog))):
        mp = []
        for j in range(len(muFog)):
            mp.append(rit[j + y][2])
        DistMatrix.append(mp)
        y += len(muFog)

    '''Calcolo il numero di nodi fog da avere attivi'''
    NF=(fogN*rho*K)/(K-1)
    if NF == int(NF):
        NF=int(NF)
    else:
        NF=int(NF)+1
    print(NF)
    #Chiudo la connessione al Data Base
    functions.stop(conne)

'''Ho modificato l'algoritmo mutUniformInt per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte '''
def mutUniformfog(individual, indpb):
    global sorN, fogN, NF
    for i in range(sorN):
        if random.random() < indpb:
            individual[i] = random.randint(0,NF-1)
    for i in range(NF):
        if random.random() < indpb:
            sost = individual[sorN + i]
            while sost in individual[sorN:]:
                sost = random.randint(0,fogN-1)
    return individual,
'''Ho modificato l'algoritmo cxUniform per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte'''
def cxUniformFog(ind1,ind2,indpb):
    global NF, sorN, fogN
    size = min(len(ind1), len(ind2))
    for i in range(sorN):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    for i in range(NF):
        if random.random() < indpb:
            if ind1[sorN+ i] not in ind2[sorN:] and ind2[sorN+i] not in ind1[sorN:]:
                ind1[sorN+i], ind2[sorN+i] = ind2[sorN+i], ind1[sorN+i]
    return ind1, ind2
'''Funzione che inizializza gli stumenti necessari per l'esecuzione dell'algoritmo genetico'''
def init_ga():
    global toolbox
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox.register("individual",load_individuals,creator.Individual,sorN,fogN,NF)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cxUniformFog,indpb=0.5)
    toolbox.register("mutate", mutUniformfog, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=7)

'''Funzione che grafica i dati passati come parametri'''
def plot_data(x,y1,y2=None):
    
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
'''Funzione che avvia l'esecuzione dell'algoritmo genetico'''
def solve_ga_Simple(cxbp,mutpb):
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
    
    
    gen=log.select("gen")
    mins=log.select("min")
    stds=log.select("std")
    
    plot_data(gen,mins,stds)


def main():
    global sources, fogs, rit, target
    #random.seed(64)
    
    #decidere: 
    rho = 0.5
    cxbp = 0.5
    mutpb = 0.3
    K = 4
    #delta mu
    mu = 0.1

    lam = (rho * mu * fogN) / sorN
    init_problem(lam,mu,rho,K)
    init_ga()
    solve_ga_Simple(cxbp,mutpb)

if __name__ == "__main__":
    main()