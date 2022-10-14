import os.path
import json
import numpy as np

from .genproblem import get_problem
from ..opt_service.optimize import send_response, solve_problem, available_algorithms
# from ..ga.ga import solve_problem

config = {
    'nchain_fog': 0.4,
    'nsrv_chain': 5,
    'nfog': 10,
    'tchain': 10.0,
    'rho': 0.6,
    'enable_network': True,
    'response': "file://sample_output.json",
}

nrun          = 10
nservices     = [3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
rhos          = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
nfogs         = [5, 10, 15, 20, 25]
delta_tchains = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2]

# nrun      = 2
# nservices = [3, 5]
# rhos      = [0.5, 0.7]
# nfogs     = [10, 15]

def nhop(data):
    nhop = 0
    for sc in data['servicechain']:
        ms = data['servicechain'][sc]['services']
        prevfog = None
        for s in ms:
            curfog = data['microservice'][s]
            if prevfog is not None and curfog != prevfog:
                nhop += 1
            prevfog = curfog
    return nhop / len(data['servicechain'])


def jain(data):
    rho = []
    for f in data['fog']:
        rho.append(data['fog'][f]['rho'])
    cv = np.std(rho) / np.mean(rho)
    return 1.0 / (1.0 + (cv**2))


def valid_solution(data):
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
    if 'deltatime' in data['extra']:
        return data['extra']['deltatime']
    else:
        return 0.0


def generations(data):
    if 'conv_gen' in data['extra']:
        return data['extra']['conv_gen']
    else:
        return 0.0

def parse_result(fname, algo):

    with open(fname, 'r') as f:
        data = json.load(f)
        if not valid_solution(data):
            return None
        j = jain(data)
        (r, s) = resp(data)
        h = nhop(data)
        gt = gatime(data)
        gen = generations(data)

        return {
                'jain': j,
                'tresp_avg': r,
                'tresp_std': s,
                'nhop': h,
                'gatime': gt,
                'convgen': gen,
                }     


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
        keys = res[0].keys()
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


def run_experiment(par, values, nrun, config, mult, outfile):
    config['nchain'] = int(config['nchain_fog'] * config['nfog'])
    orig_param = config[par]
    result = []
    for algo in available_algorithms:
        for val in values:
            res = []
            print("Experiment: %s=%.1f\t" % (par, val), end="", flush=True)
            for nr in range(nrun):
                if mult < 0:
                    fname = f"sample/output_{par}{val}_{algo.name}_run{nr}.json"
                else:
                    fname = f"sample/output_{par}{int(val*mult)}_{algo.name}_run{nr}.json"
                config[par] = val
                config['response'] = f"file://{fname}"
                if os.path.isfile(fname):
                    print("K", end="", flush=True)
                else:
                    print("R", end="", flush=True)
                    p = get_problem(config)
                    sol = solve_problem(p, algo)
                    send_response(sol)
                # parse results
                r = parse_result(fname, algo)
                if r is not None:
                    res.append(r)
                    print("+", end="", flush=True)
                else:
                    print("-", end="", flush=True)
            # newline
            print("")
            # compute average over multiple runs
            cr = collect_results(res)
            cr = {par: val} | cr
            result.append(cr)
        dump_result(result, outfile+f'{algo.name}.data')
    config[par] = orig_param


run_experiment("nsrv_chain", nservices, nrun, config, -1, "sample/sens_nsrv_chain")
run_experiment("rho", rhos, nrun, config, 10, "sample/sens_rho")
config['nsrv_chain'] = 10
run_experiment("nfog", nfogs, nrun, config, -1, "sample/sens_nfog")

config = {
    'nchain_fog': 1.0 / 3,
    'nsrv_chain': 3,
    'nfog': 3,
    'tchain': 10.0,
    'rho': 0.3,
    'enable_network': True,
    # delta_tchain = network/tchain
    'response': "file://sample_output.json",
    }

run_experiment("nfog", [3], 1, config, -1, "sample/sample")