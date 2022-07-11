#!/usr/bin/python3
import random
import sys
import numpy
import time
import json
import argparse
import requests
from deap import base
from deap import creator
from deap import tools
from deap import algorithms

sys.path.append('../FogProblem')
from problem import Problem
from solution import Solution
from fogindividual import FogIndividual



#numGen = 600    # number fo generations used in the GA
#numPop = 600    # initial number of individuals at gen0
numGen  = 60     # number fo generations used in the GA
numPop  = 60     # initial number of individuals at gen0
problem = None

# Given an individual returns the value in the obj function
def obj_func(individual1):
    # FIXME: should remove this global dependency!
    global problem
    ind = FogIndividual(individual1, problem)
    return ind.obj_func(),

def load_individuals(creator, problem:Problem):
    individual = list()
    for i in range(problem.get_nservice()):
        individual.append(random.randint(0,problem.get_nfog()-1))
    return creator(individual)
        
# Mutation of an individual
def mut_uniform_fog(individual, indpb):
    # FIXME: should remove this global dependency!
    global problem
    for i in range(len(individual)):
        if random.random() < indpb:
            individual[i] = random.randint(0,problem.get_nfog()-1)
    return individual,

# Mating of two individual
def cx_uniform_fog(ind1, ind2, indpb):
    # FIXME: should remove this global dependency!
    global problem
    size = min(len(ind1), len(ind2))
    for i in range(size):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    return ind1, ind2

# Population's initialization for the GA 
def init_ga(problem:Problem):
    toolbox = base.Toolbox()
    try:
        del creator.FitnessMin
        del creator.Individual
    except AttributeError:
        pass

    # Creation of population and individuals
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox.register("individual",load_individuals, creator.Individual, problem)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cx_uniform_fog,indpb=0.5)
    toolbox.register("mutate", mut_uniform_fog, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=7)
    return toolbox

"""
Given the best individual in the population
returns the convergence of the GA problem
"""
def get_convergence(log, min_obj:FogIndividual.obj_func, eps=0.01):
    #gen = log.select("gen")
    #stds = log.select("std")
    mins = log.select("min")
    convgen =- 1
    for i in range(len(mins)):
        if (convgen<0) and ((mins[i]/min_obj)-1.0 <eps):
            convgen = i
        #print(mins[i], stds[i])
    #print(convgen)
    return convgen

""" 
GA solver where:
 - cbxp is the probability of mating two individuals
 - mutpb the probability of mutating an individual
"""
def solve_ga_simple(toolbox:base.Toolbox, cxbp, mutpb, problem:Problem):
    # FIXME: should remove this global dependency!
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
    best = FogIndividual(hof[0], problem)
    convergence = get_convergence(log, best.obj_func())
    best.set_convergence_gen(convergence)
    #gen=log.select("gen")
    #mins=log.select("min")
    #stds=log.select("std")
    #plot_data(gen,mins,stds)
    return best

def dump_solution(gaout, sol:Solution):
    with open(gaout, "w+") as f:
            json.dump(sol.dump_solution(), f, indent=2)

def solve_problem(data):
    # FIXME: should remove this global dependency!
    global problem
    cxbp = 0.5 # Probability of mating two individuals
    mutpb = 0.3 # Probability of mutating two individuals
    problem = Problem(data)
    toolbox = init_ga(problem)
    ts = time.time()
    sol = solve_ga_simple(toolbox, cxbp, mutpb, problem)
    deltatime = time.time()-ts
    sol.registertime(deltatime)
    resp = data['response']
    if resp.startswith('file://'):
        dump_solution(resp.lstrip('file://'), sol)
    else:
        # use requests package to send results
        requests.post(data['response'], json=sol.dump_solution())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='input file. Default sample_input2.json')
    args = parser.parse_args()
    fname = args.file if args.file is not None else 'sample_input2.json'
    with open(fname,) as f:
        data = json.load(f)
    solve_problem(data)


