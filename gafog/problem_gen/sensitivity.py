import sqlite3
import json
import argparse
import threading
import multiprocessing as mp
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
    
def obj_fun_comp_score(data):
    return data['extra']['obj_func_components']

def obj_fun_score(data):
    return data['extra']['obj_func']
    
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
            obj_fun = obj_fun_score(data)
            obj_fun_components = obj_fun_comp_score(data)
            obj_fun_components_conv = obj_fun_comp_convergence(data)

            return {
                    'jain': j,
                    'tresp_avg': r,
                    'tresp_std': s,
                    'nhop': h,
                    'deltatime': gt,
                    'convgen': gen,
                    'obj_fun': obj_fun,
                    } | obj_fun_components | obj_fun_components_conv

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


def get_opt_val_key(optimizer_param, val):
    return f'{optimizer_param}_{val}' if val is not None else 'default'
    # return val

def get_prob_val_key(problem_par, val):
    return f'{problem_par}_{val}'


def _processWorker_experiment_run(run_idx, 
                                  problem_par, prob_val, 
                                  problem_config, optimizer_config, 
                                  optimizer_param,
                                  algo, mult, 
                                  best_sol_dump, 
                                  optimizer_values_iterator
                                  ):
    
    """
    Task body for every process worker. It runs all necessary experiments for a single run (it takes into consideration each 
    optimizer scenario specified)
    """

    print(f'SCENARIO {problem_par}:{prob_val} {optimizer_param}{optimizer_values_iterator} - run {run_idx} - STARTED', flush=True)
    problem = get_problem(problem_config)
    problem.set_optimizer_parameters_dict(optimizer_config)
    local_value_results = dict({
        get_opt_val_key(optimizer_param, opt_value): list() for opt_value in optimizer_values_iterator 
    })

    for opt_value in optimizer_values_iterator:
        # Fukebane creation
        optimizer_string = f'{optimizer_param}{opt_value}_' if opt_value is not None else ''
        problem_string = f'{problem_par}{prob_val if mult < 0 else int(prob_val*mult)}'

        fname = f'sample/output_' + problem_string + '_' + optimizer_string + f'run{run_idx}.json'

        # Run outcome string
        result_str = f'Run {run_idx} - {problem_par}: {prob_val} - {optimizer_param}: {opt_value} - '

        if os.path.isfile(fname):
            result_str += 'CAHCED - '
        else:
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
            local_value_results[get_opt_val_key(optimizer_param, opt_value)].append(res) 
            print(result_str + 'SUCCESS', flush=True)
        else:
            print(result_str + 'FAILED', flush=True)
    
    return local_value_results


def run_experiment_db(problem_par, problem_values, 
                      nrun, config, mult, 
                      algorithm='GA', 
                      optimizer_param=None, optimizer_values=None, 
                      best_sol_dump=False,
                      db_file='experiment_analysis/experiments.db'
                      ) -> None:
    """
    Variant of 'run_experiment' that saves the results to database.
    The 'algorithm' parameter allows to pick which algorithm to experiment on.
    """

    db_schema = None
    db_initialized = False
    database_lock = threading.Lock()

    problem_config = config['problem']
    optimizer_config = config['optimizer']

    problem_config['nchain'] = int(problem_config['nchain_fog'] * problem_config['nfog'])

    algo = algorithm_by_name(algorithm)  # The ability to iterate over algorithms has been removed due to the addition of optimizer_param

    optimizer_values_iterator = optimizer_values if optimizer_values is not None else list([None])

    def _aggregate_local_results(dict1: dict, dict2: dict):
        ret = dict()

        for key in dict1.keys() | dict2.keys():
            ret[key] = dict1.get(key, []) + dict2.get(key, [])
        return ret


    def _threadWorker_problem_scenario(problem_conf: dict, problem_par: str, problem_val, pool, db_file: str):
        """
        Task body for every thread worker. Its duty is to feed the process pool with experiment run instances,
        then it aggregates and inserts the results into the database
        """

        # These database variables are shared between threads
        nonlocal db_schema
        nonlocal db_initialized
        nonlocal database_lock

        problem_conf_scenario = deepcopy(problem_conf)
        problem_conf_scenario[problem_par] = problem_val
        value_results = dict({
            get_opt_val_key(optimizer_param, opt_value): list() for opt_value in optimizer_values_iterator 
        })

        processes_args = [(i, 
                           problem_par, problem_val, 
                           problem_conf_scenario, optimizer_config, 
                           optimizer_param, 
                           algo, mult,
                           best_sol_dump,
                           optimizer_values_iterator
                           ) for i in range(nrun)]
        
        local_results = pool.starmap(_processWorker_experiment_run, processes_args)

        for loc_res in local_results:
            value_results = _aggregate_local_results(value_results, loc_res)

        for opt_value in optimizer_values_iterator:

            opt_key = get_opt_val_key(optimizer_param, opt_value)
            
            optimizer_config_scenario = deepcopy(optimizer_config)

            if optimizer_param is not None:
                optimizer_config_scenario[optimizer_param] = opt_value

            experiment_res_scenario = collect_results(value_results[opt_key])

            with database_lock:  # Using a lock to make sure the db transaction don't interfere with each other
                db_connection = sqlite3.connect(db_file)

                if not db_initialized:
                    db_schema = create_schema(problem_config=problem_conf_scenario,
                                            optimizer_config=optimizer_config_scenario,
                                            experiment_result=experiment_res_scenario
                                            )
                    
                    init_db(db_connection, db_schema)

                    db_initialized = True
                    print(f'\nDB INITIALIZED {db_file}')
                
                insert_experiment(db_connection, 
                                problem_config=problem_conf_scenario, 
                                optimizer_config=optimizer_config_scenario, 
                                experiment_result=experiment_res_scenario,
                                schema=db_schema
                                )
                db_connection.commit()
                db_connection.close()
    

    print(f'\n{algo.name}')
    
    threads = list[threading.Thread]()  # List to keep track of all the threads created
    multiproc_pool = mp.Pool(processes=mp.cpu_count())  # Pool of all available worker processes (one process for each CPU croe)
    
    for val in problem_values:  # Creating and launching a thread for each problem scenario
        scenario_thread = threading.Thread(target=_threadWorker_problem_scenario, args=(problem_config, problem_par, val, multiproc_pool, db_file))
        threads.append(scenario_thread)
        scenario_thread.start()
    
    for thread in threads:  # Barrier to make sure every thread of the pool finished its work
        thread.join()
    
    


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
