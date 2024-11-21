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
#numGen = 10    # number fo generations used in the GA
#numPop = 10    # initial number of individuals at gen0
#problem = None

DEFAULT_CXPB = 0.5
DEFAULT_MUTPB = 0.3

def init_ga(problem: Problem):
    problem_type=problem.get_problem_type()
    #print(f'problem type: {problem_type}')
    if problem_type == 'ProblemPerf':
        from .ga_perf import init_ga as initga
        return initga(problem)
    if problem_type == 'ProblemPwr':
        from .ga_pwr import init_ga as initga
        return initga(problem)


def get_convergence(log_fitness, min_obj, eps=0.01):
    # gen=log.select("gen")
    # stds = log.select("std")
    mins = log_fitness.select("min")
    convgen = -1
    for i in range(len(mins)):
        if (mins[i] / min_obj) - 1.0 < eps:
            convgen = i
            # print(mins[i], stds[i], convgen)
            break
    # print(convgen)
    return convgen

def get_obj_components_convergence(log_solution, min_obj_components, eps=0.01):

    def comp_converged(component_val, component_min, eps):
        ret = False

        if component_min == 0 and component_val == 0:
            ret = True
        elif component_min != 0:
            ret = ((abs(component_val - component_min)) / (component_min)) < eps
        return ret

    generations_best_sol = log_solution.select('best_individual')
    component_convergence = dict({
        key: None for key in min_obj_components.keys()
    })

    for i in range(len(generations_best_sol)):
        sol_components = generations_best_sol[i].get_obj_func_components()

        for component in component_convergence.keys():
            if (component_convergence[component] is None 
                and comp_converged(sol_components[component], min_obj_components[component], eps)):
                component_convergence[component] = i

        if numpy.all([convergence_it is not None for convergence_it in component_convergence.values()]):
            break

    return component_convergence


def solve_ga_simple(toolbox, cxpb, mutpb, problem:Problem, filename_best_dump=None, delimiter='\t'):
    # FIXME: should remove this global dependency!
    # GA solver
    # TODO: MOVE THESE TWO CONSTANTS INTO THE PROBLEM 'OPTIMIZER' PARAMETERS
    global numPop, numGen
    pop = toolbox.population(n=numPop)
    # save best solution in Hall of Fame
    hof = tools.HallOfFame(1)
    # initialize Logbook to save statistics
    # https://deap.readthedocs.io/en/master/tutorials/basic/part3.html
    log = tools.Logbook()

    fitness_stats = tools.Statistics(lambda ind: ind.fitness.values)
    fitness_stats.register("avg", numpy.mean)
    fitness_stats.register("std", numpy.std)
    fitness_stats.register("min", numpy.min)
    fitness_stats.register("max", numpy.max)

    # Adding some statistics to monitor the evolution of the best solution of each generation
    solution_stats = tools.Statistics(lambda ind: ind)
    def __best_ind(individuals):
        """
        Statistics function that returns the individual with the best (min) obj func value,
        the individual is returned as an instance of the appropriate "Solution" class
        """
        best_ind_index = numpy.argmin([ind.fitness.values for ind in individuals])
        return problem.get_solution(individuals[best_ind_index])
    
    def __best_ind_fitness(individuals):
        """
        Statistics function that returns the obj function value of the best individual for
        each generation (the only purpose of this function is to validate the best solution
        recorded in the logs)
        """
        best = __best_ind(individuals)
        return best.obj_func()

    solution_stats.register("best_individual", __best_ind)
    # solution_stats.register("fitness_best_ind", __best_ind_fitness)

    multi_statistics = tools.MultiStatistics(fitness=fitness_stats, solution=solution_stats)

    # Change verbose parameter to see population evolution
    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=cxpb, mutpb=mutpb, ngen=numGen, 
                                    stats=multi_statistics, halloffame=hof, verbose=False)
    best = problem.get_solution(hof[0])
    convergence = get_convergence(log.chapters['fitness'], best.obj_func())
    components_convergence = get_obj_components_convergence(log.chapters['solution'], best.get_obj_func_components())
    best.set_extra_param('conv_gen', convergence)
    best.set_extra_param('components_conv', components_convergence)
    best.set_extra_param('max_gen', numGen)
    best.set_extra_param('population', numPop)
    # gen=log.select("gen")
    # mins=log.select("min")
    # stds=log.select("std")
    # plot_data(gen,mins,stds)
    
    # print(log)
    if filename_best_dump is not None:

        gen_idx_arr = numpy.array(log.chapters['solution'].select("gen"))

        best_list = log.chapters['solution'].select("best_individual")
        best_arr = numpy.array([f'"{str(best)}"' for best in best_list])

        obj_fun_components = [sol.get_obj_func_components() for sol in best_list]
        component_lists = dict()
        for comp in obj_fun_components:
            for key in comp.keys():
                if component_lists.get(key, None) is None:
                    component_lists[key] = list()
                component_lists[key].append(comp[key])

        header = delimiter.join(['gen'] + [key for key in component_lists.keys()] + ['best_sol'])
        columns = (gen_idx_arr,) + tuple([numpy.array(comp_list) for comp_list in component_lists.values()]) + (best_arr,)

        numpy.savetxt(filename_best_dump, numpy.transpose(columns), comments='#', header=header, delimiter=delimiter, fmt='%s')

    return best


def dump_solution(gaout, sol: Solution):
    with open(gaout, "w+") as f:
        json.dump(sol.dump_solution(), f, indent=2)


def solve_problem(problem: Problem, filename_best_dump=None, delimiter='\t'):

    problem.begin_solution()
    toolbox = init_ga(problem)
    sol = solve_ga_simple(toolbox, problem.get_optimizer_parameter('cxpb'), problem.get_optimizer_parameter('mutpb'), problem, filename_best_dump=filename_best_dump, delimiter=delimiter)
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
    parser.add_argument('-b', '--best-gen-file', help=f'filename of the file used to log the best solution of each generation')
    parser.add_argument('-d', '--column-delimiter', help='delimiter used to separate each column in the specified "best solutions file" (works only if -b has been specified)')

    args = parser.parse_args()
    fname = args.file or f'{DEFAULT_DIR}/{DEFAULT_INPUT}'
    with open(fname) as f:
        data = json.load(f)
    # FIXME: use problem loader
    problem=load_problem(data)

    problem.set_optimizer_parameters_dict(dict({
        'cxpb': DEFAULT_CXPB,
        'mutpb': DEFAULT_MUTPB,
    }))

    solve_problem_kwargs = dict()
    if args.best_gen_file is not None:
        solve_problem_kwargs['filename_best_dump'] = args.best_gen_file
    if args.column_delimiter is not None:
        solve_problem_kwargs['delimiter'] = args.column_delimiter

    sol = solve_problem(problem, **solve_problem_kwargs)
    print(sol)

    fname = args.output or f'{DEFAULT_DIR}/{DEFAULT_OUTPUT}'
    with open(fname, "w") as f:
        json.dump(sol.dump_solution(), f, indent=2)
