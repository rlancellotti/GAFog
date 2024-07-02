import sqlite3
import json
import argparse
import os.path

import numpy as np

from copy import deepcopy

from .genproblem import get_problem
from .analysis_db import create_schema, init_db, insert_experiment, print_table
from ..opt_service.optimize import send_response, solve_problem, available_algorithms, algorithm_by_name
# from ..ga.ga import solve_problem

config_example = {
    'problem': {
        'type': 'power',
        'nchain_fog': 0.4,
        'nsrv_chain': 5,
        'nfog': 10,
        'tchain': 10.0,
        'rho': 0.6,
        'enable_network': True,
        'delta_tchain': 0.05,
        'response': "file://sample_output.json",
    },
    'optimizer':{
        'type': 'GA',
        'cxpb': 0.5,
        'mutpb': 0.3,
        'mutation_params': {
            'shprob': 0.5
        }
    }
}

#DEFAULT_NRUN          = 10
#nservices     = [3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
#rhos          = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#nfogs         = [5, 10, 15, 20, 25]
#delta_tchains = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2]

DEFAULT_NRUN = 2
nservices = [3, 5]
rhos      = [0.5, 0.7]
nfogs     = [10, 15]

def nhop(data):
    nhop = 0
    for sc in data['servicechain']:
        ms = data['servicechain'][sc]['services']
        prevfog = None
        for s in ms:
            curfog   = data['microservice'][s]
            if prevfog is not None and curfog != prevfog:
                nhop += 1
            prevfog  = curfog
    return nhop / len(data['servicechain'])

def jain(data):
    rho = []
    for f in data['fog']:
        rho.append(data['fog'][f]['rho'])
    cv = np.std(rho) / np.mean(rho)
    return 1.0 / (1.0 + (cv**2))

def valid_solution(data):
    """ A valid solutiona have all the rho of the nodes < 1. """ 

    for f in data['fog']:
        if data['fog'][f]['rho'] >= 1:
            return False
    return True

def resp(data):
    # print(data)
    tr = []
    for sc in data['servicechain']:
        tr.append(data['servicechain'][sc]['resptime'])
    return (np.mean(tr), np.std(tr))

def gatime(data):
    """ Returns the execution time. """
    
    if 'deltatime' in data['extra']:
        return data['extra']['deltatime']
    else:
        return 0.0

def generations(data):
    if 'conv_gen' in data['extra']:
        return data['extra']['conv_gen']
    else:
        return 0.0
    
def obj_fun_comp_convergence(data):
    if 'components_conv' in data['extra']:
        return {key + '_convgen': val for key, val in data['extra']['components_conv'].items()}

def parse_result(fname):

    with open(fname, 'r') as f:
        data = json.load(f)

        if valid_solution(data):
            j = jain(data)
            (r, s) = resp(data)
            h = nhop(data)
            gt = gatime(data)
            gen = generations(data)
            obj_fun_component_conv = obj_fun_comp_convergence(data)

            return {
                    'jain': j,
                    'tresp_avg': r,
                    'tresp_std': s,
                    'nhop': h,
                    'deltatime': gt,
                    'convgen': gen,
                    } | obj_fun_component_conv

def collect_results(res):
    rv = {}
    if len(res) > 0:
        for k in res[0].keys():
            samples = []
            for r in res:
                samples.append(r[k])
            rv[k] = np.mean(samples)
            rv['sigma_%s' % k] = np.std(samples)
    return rv

def dump_result(res, fname):
    with open(fname, 'w') as f:
        # heading
        # The max over a list comprehension ensures that even if the first experiment fails all runs we still get an appropriate heading
        keys = max([r.keys() for r in res], key=lambda x : len(x))
        s = "#"
        for k in keys:
            s = '%s%s\t' % (s, k)
        f.write(s + '\n')
        # lines
        for r in res:
            s = ""
            for k in keys:
                if k in r.keys():
                    s = '%s%f\t' % (s, r[k])
                else:
                    s = '%s0\t' % (s)
            f.write(s + '\n')


def run_experiment(par, values, nrun, config, mult, algorithm='GA', optimizer_param=None, optimizer_values=None, best_sol_dump=False) -> dict:
    """
    The 'algorithm' parameter allows to pick which algorithm to experiment on.
    Returns a dictionary that keeps the results of each experiment with respects divided in two diffenrent collections,
    one focused problem scenarios and the other optimizer scenarios.
    """

    def get_opt_val_key(val):
        return f'{optimizer_param}_{val}' if val is not None else 'default'
        # return val

    def get_prob_val_key(val):
        return f'{par}_{val}'

    problem_config = config['problem']
    optimizer_config = config['optimizer']

    problem_config['nchain'] = int(problem_config['nchain_fog'] * problem_config['nfog'])
    orig_param = problem_config[par]

    algo = algorithm_by_name(algorithm)  # The ability to iterate over algorithms has been removed due to the addition of optimizer_param

    optimizer_values_iterator = optimizer_values if optimizer_values is not None else list([None])

    algo_results = dict()

    
    print(f'\n{algo.name}')
    results = {
        'problem_val': dict({get_opt_val_key(opt_value): list() for opt_value in optimizer_values_iterator}),
        'optimizer_val': dict({get_prob_val_key(prob_value): list() for prob_value in values}
                                ) if optimizer_param is not None else None
    }
    
    
    for val in values:

        value_results = dict({
            get_opt_val_key(opt_value): list() for opt_value in optimizer_values_iterator 
        })

        print(f'Experiment: {par}={val} ', end='', flush=True)

        for run_idx in range(nrun):
            print(f'(Run {run_idx}:', end='', flush=True)
            problem_config[par] = val
            problem = get_problem(problem_config)
            problem.set_optimizer_parameters_dict(optimizer_config)

            for opt_value in optimizer_values_iterator:
                optimizer_string = f'{optimizer_param}{opt_value}_' if opt_value is not None else ''
                problem_string = f'{par}{val if mult < 0 else int(val*mult)}'

                fname = f'sample/output_' + problem_string + '_' + optimizer_string + f'run{run_idx}.json'

                if os.path.isfile(fname):
                    print('K', end='', flush=True)
                else:
                    print('R', end='', flush=True)
                    problem.set_response_url(f'file://{fname}')
                    if opt_value is not None:
                        problem.set_optimizer_parameter(optimizer_param, opt_value)

                    best_sol_file = None
                    if best_sol_dump:
                        best_sol_file = f'best_sol_dumps/sens_' + problem_string + '_' + optimizer_string + f'_run{run_idx}.csv'

                    sol = solve_problem(problem, algo, filename_best_dump=best_sol_file)
                    send_response(sol)
                
                res = parse_result(fname)
                if res is not None:
                    value_results[get_opt_val_key(opt_value)].append(res) 
                    print('+', end='', flush=True)
                else:
                    print('-', end='', flush=True)
            
            print(')', end='', flush=True)
            
        for opt_value in optimizer_values_iterator:

            opt_key = get_opt_val_key(opt_value)


            results['problem_val'][opt_key].append({par: val} | collect_results(value_results[opt_key]))

            if opt_value is not None:
                results['optimizer_val'][get_prob_val_key(val)].append({optimizer_param: opt_value} | collect_results(value_results[opt_key]))

            print('')
        
        algo_results[algo.name] = results

    problem_config[par] = orig_param

    return algo_results


def run_experiment_db(par, values, 
                      nrun, config, mult, 
                      algorithm='GA', 
                      optimizer_param=None, optimizer_values=None, 
                      best_sol_dump=False,
                      db_file='experiment_analysis/experiments.db'
                      ) -> None:
    """
    Variant of 'run_experiment_db' that saves the results to database.
    The 'algorithm' parameter allows to pick which algorithm to experiment on.
    """

    db_connection = sqlite3.connect(db_file)
    db_schema = None
    db_initialized = False

    def get_opt_val_key(val):
        return f'{optimizer_param}_{val}' if val is not None else 'default'
        # return val

    def get_prob_val_key(val):
        return f'{par}_{val}'

    problem_config = config['problem']
    optimizer_config = config['optimizer']

    problem_config['nchain'] = int(problem_config['nchain_fog'] * problem_config['nfog'])
    orig_param = problem_config[par]

    algo = algorithm_by_name(algorithm)  # The ability to iterate over algorithms has been removed due to the addition of optimizer_param

    optimizer_values_iterator = optimizer_values if optimizer_values is not None else list([None])

    print(f'\n{algo.name}')
    
    for val in values:
        problem_config[par] = val
        value_results = dict({
            get_opt_val_key(opt_value): list() for opt_value in optimizer_values_iterator 
        })

        print(f'Experiment: {par}={val} ', end='', flush=True)

        for run_idx in range(nrun):
            print(f'(Run {run_idx}:', end='', flush=True)
            problem = get_problem(problem_config)
            problem.set_optimizer_parameters_dict(optimizer_config)

            for opt_value in optimizer_values_iterator:
                optimizer_string = f'{optimizer_param}{opt_value}_' if opt_value is not None else ''
                problem_string = f'{par}{val if mult < 0 else int(val*mult)}'

                fname = f'sample/output_' + problem_string + '_' + optimizer_string + f'run{run_idx}.json'

                if os.path.isfile(fname):
                    print('K', end='', flush=True)
                else:
                    print('R', end='', flush=True)
                    problem.set_response_url(f'file://{fname}')
                    if opt_value is not None:
                        problem.set_optimizer_parameter(optimizer_param, opt_value)

                    best_sol_file = None
                    if best_sol_dump:
                        best_sol_file = f'best_sol_dumps/sens_' + problem_string + '_' + optimizer_string + f'_run{run_idx}.csv'

                    sol = solve_problem(problem, algo, filename_best_dump=best_sol_file)
                    send_response(sol)
                
                res = parse_result(fname)
                if res is not None:
                    value_results[get_opt_val_key(opt_value)].append(res) 
                    print('+', end='', flush=True)
                else:
                    print('-', end='', flush=True)
            
            print(')', end='', flush=True)
            
        for opt_value in optimizer_values_iterator:

            opt_key = get_opt_val_key(opt_value)
            
            optimizer_config_scenario = deepcopy(optimizer_config)

            if optimizer_param is not None:
                optimizer_config_scenario[optimizer_param] = opt_value

            experiment_res_scenario = collect_results(value_results[opt_key])

            if not db_initialized:
                db_schema = create_schema(problem_config=problem_config,
                                          optimizer_config=optimizer_config_scenario,
                                          experiment_result=experiment_res_scenario
                                          )
                
                init_db(db_connection, db_schema)

                db_initialized = True
                print(f'\nDB INITIALIZED {db_file}')
            
            insert_experiment(db_connection, 
                              problem_config=problem_config, 
                              optimizer_config=optimizer_config_scenario, 
                              experiment_result=experiment_res_scenario,
                              schema=db_schema
                              )
        print('\n')
        problem_config[par] = orig_param 
        db_connection.commit()


def dump_experiment(experiment_data, outfile):
    """
    Given the dictionary returned by 'run_experiment' it saves all the results to file, each file
    represents a scenario, either a problem-scenario (the problem is fixed and the optimizer param variates)
    or an optimizer-scenario (vice-versa).
    """
    # Problem dump
    for algo in experiment_data.keys():
        # Problem data dump
        problem_data = experiment_data[algo]['problem_val']
        for opt_setting in problem_data.keys():
            dump_result(problem_data[opt_setting], outfile+f'{algo}_setting-{opt_setting}.data')
        # Optimizer data dump
        optimizer_data = experiment_data[algo]['optimizer_val']
        if optimizer_data is not None:
            for problem_setting in optimizer_data.keys():
                dump_result(optimizer_data[problem_setting], outfile+f'{algo}_setting-{problem_setting}.data')

#run_experiment("nsrv_chain", nservices, DEFAULT_NRUN, config, -1, "sample/sens_nsrv_chain", algorithm='GA')



if __name__ == "__main__":

    def get_value_type(type_str):
        if type_str is not None:
            value_type = None  # By default the values are strings
            if (len(type_str) == 1 and type_str.lower() == 'i') or type_str == 'int':
                value_type = int
            elif (len(type_str) == 1 and type_str.lower() == 'f') or type_str == 'float':
                value_type = float
        else:
            value_type = None
        return value_type

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-database', help=f'Output database to store the experiments. Default "experiment_analysis/experiments.db"', type=str)
    parser.add_argument('-p', '--parameter', help=f'Problem parameter to test on', type=str, required=True)
    parser.add_argument('-v', '--values', help=f'List of values to assign to the parameter', nargs='+', required=True, type=str)
    parser.add_argument('-t', '--value-type', help=f'type of the values listed with the -v option', required=True, type=str)
    parser.add_argument('-a', '--algorithm', help='Optimization algorithm to test on', default='GA', type=str)
    parser.add_argument('-c', '--config', help="config file. Default use default config", required=True)
    parser.add_argument('-r', '--nrun', help="number of runs for each test configuration", default=DEFAULT_NRUN, type=int)
    parser.add_argument('-m', '--mult', help="mult parameter", default=-1, type=int)
    parser.add_argument('-z', '--optimizator-parameter', help=f'Problem parameter to test on', type=str)
    parser.add_argument('-l', '--opt-values', help=f'List of values to assign to the optimizator parameter', nargs='+')
    parser.add_argument('-d', '--opt-value-type', help=f'type of the values listed with the -l option', type=str)
    parser.add_argument('-b', '--track-best-sol', action="store_true", help="Track the best solution convergence each run")

    args  = parser.parse_args()
    
    output_db = args.output_database
    if output_db is None:
        output_db = 'experiment_analysis/experiments.db'

    value_type = get_value_type(args.value_type)

    if value_type is not None:
        values = [value_type(val) for val in args.values]
    else:
        values = None

    opt_value_type = get_value_type(args.opt_value_type)

    if opt_value_type is not None:
        opt_values = [opt_value_type(val) for val in args.opt_values] if args.opt_values is not None else None
    else:
        opt_values = None

    config = json.loads(open(args.config, 'r').read())

    experiment_data = run_experiment_db(args.parameter, values, 
                                        args.nrun,  
                                        config, 
                                        args.mult, 
                                        args.algorithm, 
                                        optimizer_param=args.optimizator_parameter, 
                                        optimizer_values=opt_values,
                                        best_sol_dump=args.track_best_sol,
                                        db_file=output_db
                                        )
    
    print_table(connection=sqlite3.connect(output_db), table_name='experiment')
