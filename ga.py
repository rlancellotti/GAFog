#!/usr/bin/python3
import random
import numpy
import math
import datetime
from problem import Problem
from fogindividual import FogIndividual
import matplotlib.pyplot as plt
from collections import namedtuple

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

numGen = 500    # numero di generazioni percui continuare a fare evolevere la popolazione
numPop = 200    # numero iniziale degli individui alla prima generazione
maxrho = 0.999
gaout1 = "GA.data"
gaout2 = "GA-MG1.data"
def obj_func(individual1):
    global maxrho, problem
    # individual1=[fog_mapping]+[source_mapping]
    # fog mapping: fog_mapping[fog]=real_fog_ID
    # source mapping: source_mapping[source]=individual_fog_ID
    ind=FogIndividual(individual1, problem)
    return ind.obj_func(),
    #print(ind)
    #individual = [0]*problem.nsrc
    #for i in range(problem.nsrc):
    #    individual[i] = individual1[problem.nsrc + individual1[i]]
    #latency = 0
    # length = len(muFog)
    #length = problem.nfog
    #lambda_fog = [0] * length
    #time_fog = [0] * length
    #for i in range(problem.nsrc):
    #    lambda_fog[individual[i]] += problem.lambda_src[i]
    # num_nodi = funzioni.membriNodo(individual, lungh)
    #print(problem.nfog, len(problem.mu_fog))
    #for i in range(problem.nfog):
    #    if problem.mu_fog[i] > lambda_fog[i]:
    #        time_fog[i] = 1 / (problem.mu_fog[i] - lambda_fog[i])
    #    else:
    #        time_fog[i] = 1 / problem.mu_fog[i] * 1 / (1 - maxrho)
    #for i in range(problem.nsrc):
    #    latency += (problem.dist_matrix[i][individual[i]] + time_fog[individual[i]])
    # valid = is_valid(individual)
    #return latency,

def load_individuals(creator, problem):
    individual = list()
    for i in range(problem.nsrc):
        individual.append(random.randint(0,problem.nf-1))
    nodi = random.sample(range(problem.nfog),problem.nf)
    #print(nodi)
    individual = individual + nodi
    #print(FogIndividual(individual, problem))
    return creator(individual)
        
def mut_uniform_fog(individual, indpb):
    global problem
    for i in range(problem.nsrc):
        if random.random() < indpb:
            individual[i] = random.randint(0,problem.nf-1)
    for i in range(problem.nf):
        if random.random() < indpb:
            if problem.nf < problem.nfog:
                opt=[]
                for j in range(problem.nfog):
                    if j not in individual[problem.nsrc:]:
                        opt.append(j)
                individual[problem.nsrc + i]=random.choice(opt)
            else:
                srcidx=problem.nsrc + i
                dstidx=problem.nsrc + (i+1) % problem.nf
                individual[srcidx], individual[dstidx] = individual[dstidx], individual[srcidx]
    return individual,

'''Ho modificato l'algoritmo cxUniform per adattarlo all'esigenza:
    in particolare distingue le due parti del genoma ed evita la generazione di doppioni nella seconda parte'''
def cx_uniform_fog(ind1,ind2,indpb):
    global problem
    #size = min(len(ind1), len(ind2))
    for i in range(problem.nsrc):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    for i in range(problem.nf):
        if random.random() < indpb and ind1[problem.nsrc+i] not in ind2[problem.nsrc:] and ind2[problem.nsrc+i] not in ind1[problem.nsrc:]:
                ind1[problem.nsrc+i], ind2[problem.nsrc+i] = ind2[problem.nsrc+i], ind1[problem.nsrc+i]
    return ind1, ind2

def init_ga(problem):
    # Initialization
    toolbox = base.Toolbox()
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox.register("individual",load_individuals, creator.Individual, problem)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cx_uniform_fog,indpb=0.5)
    toolbox.register("mutate", mut_uniform_fog, indpb=0.05)
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


def solve_ga_simple(toolbox, cxbp, mutpb, problem):
    # GA solver
    global numPop, numGen
    pop = toolbox.population(n=numPop)
    # save best solution in Hall of Fame
    hof = tools.HallOfFame(1)
    # initialize Logbook to save statistics
    # https://deap.readthedocs.io/en/master/tutorials/basic/part3.html
    log = tools.Logbook()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    # Change verbose parameter to see population evolution
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=cxbp, mutpb=mutpb, ngen=numGen, 
                                   stats=stats, halloffame=hof, verbose=False)
    best=FogIndividual(hof[0], problem)
    #gen=log.select("gen")
    #mins=log.select("min")
    #stds=log.select("std")
    #plot_data(gen,mins,stds)
    return best

def dump_solution(gaout, sol):
    with open(gaout, "w+") as f:
            f.write("#type\tobjf\tnet_delay\tproc_time\n")
            f.write("\"MM1\"\t%f\t%f\t%f\n" % (sol.obj_func(), sol.network_time(), sol.processing_time()))
            f.write("\"MG1-CV01\"\t%f\t%f\t%f\n" % (sol.obj_func(systemtype='MG1', cv=0.5), sol.network_time(), sol.processing_time(systemtype='MG1', cv=0.5)))
            f.write("\"MG1-CV05\"\t%f\t%f\t%f\n" % (sol.obj_func(systemtype='MG1', cv=0.5), sol.network_time(), sol.processing_time(systemtype='MG1', cv=0.5)))
            f.write("\"MG1-CV10\"\t%f\t%f\t%f\n" % (sol.obj_func(systemtype='MG1', cv=1), sol.network_time(), sol.processing_time(systemtype='MG1', cv=1)))
            f.write("\"MG1-CV15\"\t%f\t%f\t%f\n" % (sol.obj_func(systemtype='MG1', cv=1.5), sol.network_time(), sol.processing_time(systemtype='MG1', cv=1.5)))
            #print(sol.obj_func(), sol.network_time(), sol.processing_time(), sol.lambda_tot)

problem=None
if __name__ == "__main__":
    #random.seed(64)
    #decidere: 
    rho = 0.8
    cxbp = 0.5
    mutpb = 0.3
    # K=0 -> use all fogs
    K = 0
    #delta mu
    deltamu=1
    delta = 0.01
    mu=deltamu/delta
    problem = Problem('Tesi2.db', mu, delta, rho, K, maxrho)
    toolbox=init_ga(problem)
    sol=solve_ga_simple(toolbox, cxbp, mutpb, problem)
    dump_solution(gaout1, sol)
    sol.create_omnet_files('fog', 'fog')
    sol=solve_ga_simple(toolbox, cxbp, mutpb, problem)
    dump_solution(gaout2, sol)


