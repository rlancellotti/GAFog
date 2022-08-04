#!/usr/bin/python3
import sys
import os.path
import json
import numpy as np
# Hack to find modules of other services
sys.path.append('../')
from ProblemGen.genproblem import get_problem
from FogProblem.problem import Problem
from OptService.optimize import send_response, solve_problem, available_algorithms
#from GA.ga import solve_problem

config={
    'nchain_fog': 0.4,
    'nsrv_chain': 5,
    'nfog': 10,
    'tchain': 10.0,
    'rho': 0.6,
    'enable_network': True,
    'response': 'file://sample_output.json'
}

class Sensitivity:
    def __init__(self, param_name: str, values: list, mult: float):
        self.param=param_name
        self.values=values
        self.mult=mult

    def get_values(self):
        return self.values
    
    def get_param(self):
        return self.param

nrun=2
nservices=[3, 5]
rhos=[0.5, 0.7]
nfogs=[10, 15]
#nrun=10
#nservices=[3, 4, 5, 6, 7, 8, 9, 10]
#rhos=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
#nfogs=[5, 10, 15, 20, 25]

def nhop(data):
    nhop=0
    for sc in data['servicechain']:
        ms=data['servicechain'][sc]['services']
        prevfog=None
        for s in ms:
            curfog=data['microservice'][s]
            if prevfog is not None and curfog != prevfog:
                nhop +=1
            prevfog=curfog
    return nhop/len(data['servicechain'])

def jain(data):
    rho=[]
    for f in data['fog']:
        rho.append(data['fog'][f]['rho'])
    cv=np.std(rho)/np.mean(rho)
    return 1.0/(1.0+(cv**2))

def valid_solution(data):
    for f in data['fog']:
        if data['fog'][f]['rho']>=1:
            return False
    return True

def resp(data):
    #print(data)
    tr=[]
    for sc in data['servicechain']:
        tr.append(data['servicechain'][sc]['resptime'])
    return (np.mean(tr), np.std(tr))

def gatime(data):
    return data['extra']['deltatime']

def generations(data):
    return data['extra']['conv_gen']

def parse_result(fname):
    with open(fname, 'r') as f:
        data=json.load(f)
        if not valid_solution(data):
            return None
        j=jain(data)
        (r, s)=resp(data)
        h=nhop(data)
        gt=gatime(data)
        gen=generations(data)
    return {'jain': j, 'tresp_avg': r, 'tresp_std': s, 'nhop': h, 'gatime': gt, 'convgen': gen}

def collect_results(res):
    rv={}
    if len(res)>0:
        for k in res[0].keys():
            samples=[]
            for r in res:
                samples.append(r[k])
            rv[k]=np.mean(samples)
            rv['sigma_%s'%k]=np.std(samples)
    return rv

def dump_result(res, fname):
    with open(fname, 'w') as f:
        # heading
        keys=res[0].keys()
        s='#'
        for k in keys:
            s='%s%s\t'%(s, k)
        f.write(s+'\n')
        # lines
        for r in res:
            s=''
            for k in keys:
                if k in r.keys():
                    s='%s%f\t'%(s, r[k])
                else:
                    s='%s0\t'%(s)
            f.write(s+'\n')


def run_experiment(par: str, values: list, nrun: int, config: dict, mult: float, outfile: str):
    config['nchain']=int(config['nchain_fog']*config['nfog'])
    orig_param=config[par]
    result=[]
    for algo in available_algorithms:
        for val in values:
            res=[]
            print('Experiment: %s=%.1f\t'%(par,val), end='')
            sys.stdout.flush()
            for nr in range(nrun):
                if mult<0:
                    fname=f'output_{par}{val}_{algo.name}_run{nr}.json'
                else:
                    fname=f'output_{par}{int(val*mult)}_{algo.name}_run{nr}.json'
                config[par]=val
                config['response']=f'file://{fname}'
                if os.path.isfile(fname):
                    print('K', end='')
                else:
                    print('R', end='')
                    p=get_problem(config)
                    sol=solve_problem(p, algo)
                    send_response(sol)
                sys.stdout.flush()
                #parse results
                r=parse_result(fname)
                if r is not None:
                    res.append(r)
                    print('+', end='')
                else:
                    print('-', end='')
                sys.stdout.flush()
            # newline
            print('')
            #compute average over multiple runs
            cr=collect_results(res)
            cr= {par: val} | cr
            result.append(cr)
        dump_result(result, outfile)
    config[par]=orig_param

run_experiment('nsrv_chain', nservices, nrun, config, -1, 'sens_nsrv_chain.data')
run_experiment('rho', rhos, nrun, config, 10, 'sens_rho.data')
config['nsrv_chain']=10
run_experiment('nfog', nfogs, nrun, config, -1, 'sens_nfog.data')

config={
    'nchain_fog': 1.0/3,
    'nsrv_chain': 3,
    'nfog': 3,
    'tchain': 10.0,
    'rho': 0.3,
    'enable_network': True,
    'response': 'file://sample_output.json'
}

run_experiment('nfog', [3], 1, config, -1, 'sample.data')
