#!/usr/bin/env python3
import random
import numpy
import time
import json
import argparse
from collections import namedtuple
from deap import base, creator, tools, algorithms

from ..fog_problem.problem import Problem, load_problem
from ..fog_problem.solution import Solution

numGen = 600    # number fo generations used in the GA
numPop = 600    # initial number of individuals at gen0
#numGen = 60    # number fo generations used in the GA
#numPop = 60    # initial number of individuals at gen0
#problem = None


def init_ga(problem: Problem):
    problem_type=problem.get_problem_type()
    #print(f'problem type: {problem_type}')
    if problem_type == 'ProblemPerf':
        from .ga_perf import init_ga as initga
        return initga(problem)
    if problem_type == 'ProblemPwr':
        from .ga_pwr import init_ga as initga
        return initga(problem)


def get_convergence(log, min_obj, eps=0.01):
    # gen=log.select("gen")
    # stds = log.select("std")
    mins = log.select("min")
    convgen = -1
    for i in range(len(mins)):
        if (mins[i] / min_obj) - 1.0 < eps:
            convgen = i
            # print(mins[i], stds[i], convgen)
            break
    # print(convgen)
    return convgen


def solve_ga_simple(toolbox, cxbp, mutpb, problem:Problem):
    # FIXME: should remove this global dependency!
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
    best = problem.get_solution(hof[0])
    convergence = get_convergence(log, best.obj_func())
    best.set_extra_param('conv_gen', convergence)
    best.set_extra_param('max_gen', numGen)
    best.set_extra_param('population', numPop)
    # gen=log.select("gen")
    # mins=log.select("min")
    # stds=log.select("std")
    # plot_data(gen,mins,stds)
    return best


def dump_solution(gaout, sol: Solution):
    with open(gaout, "w+") as f:
        json.dump(sol.dump_solution(), f, indent=2)


def solve_problem(problem: Problem):
    cxbp = 0.5
    mutpb = 0.3
    problem.begin_solution()
    toolbox = init_ga(problem)
    sol = solve_ga_simple(toolbox, cxbp, mutpb, problem)
    problem.end_solution()
    sol.register_execution_time()
    return sol

DEFAULT_DIR='sample'
DEFAULT_INPUT='sample_input_pwr2.json'
DEFAULT_OUTPUT='sample_output_pwr2.json'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help=f'input file. Default {DEFAULT_DIR}/{DEFAULT_INPUT}')
    parser.add_argument('-o', '--output', help=f'output file. Default {DEFAULT_DIR}/{DEFAULT_OUTPUT}')

    args = parser.parse_args()
    fname = args.file or f'{DEFAULT_DIR}/{DEFAULT_INPUT}'
    with open(fname) as f:
        data = json.load(f)
    # FIXME: use problem loader
    problem=load_problem(data)
    sol = solve_problem(problem)
    print(sol)

    fname = args.output or f'{DEFAULT_DIR}/{DEFAULT_OUTPUT}'
    with open(fname, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)
