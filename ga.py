#!/usr/bin/python3
import random
import numpy
import math
import datetime
from problem import Problem
from fogindividual import FogIndividual
import matplotlib.pyplot as plt
from collections import namedtuple
import json

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

numGen = 1    # number fo generations used in the GA
numPop = 50    # initial number of individuals at gen0
gaout = "GA.data"

def obj_func(individual1):
    global problem
    ind=FogIndividual(individual1, problem)
    return ind.obj_func(),

def load_individuals(creator, problem):
    individual = list()
    for i in range(problem.get_nservice()):
        individual.append(random.randint(0,problem.get_nfog()-1))
    return creator(individual)
        
def mut_uniform_fog(individual, indpb):
    global problem
    for i in range(problem.get_nservice()):
        if random.random() < indpb:
            individual[i] = random.randint(0,problem.get_nfog()-1)
    return individual,

def cx_uniform_fog(ind1,ind2,indpb):
    global problem
    #size = min(len(ind1), len(ind2))
    for i in range(problem.get_nservice()):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
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
    # FIXME must consider new solution model!
    with open(gaout, "w+") as f:
            json.dump(sol.dump_solution(), f, indent=2)
            # f.write("#type\tobjf\n")
            # f.write("\"MG1-CV01\"\t%f\n" % sol.obj_func())
            # print(sol.obj_func(), sol.network_time(), sol.processing_time(), sol.lambda_tot)

problem=None
if __name__ == "__main__":
    #random.seed(64)
    cxbp = 0.5
    mutpb = 0.3
    with open('sample_input.json',) as f:
        data = json.load(f)
    problem=Problem(data)
    toolbox=init_ga(problem)
    sol=solve_ga_simple(toolbox, cxbp, mutpb, problem)
    dump_solution(gaout, sol)


