#!/usr/bin/python3
from mako.template import Template
from mako.runtime import Context
import json

def get_filename(ftemplate):
    return ftemplate.replace('.mako', '')

def process_template(ftemplate, sol):
    fout = get_filename(ftemplate)
    #FIXME: should infer contents based on object content
    mapping=json.load(open(sol, 'r'))
    #print(problem, mapping)
    mytemplate=Template(filename=ftemplate)
    with open(fout, "w") as f:
        f.write(mytemplate.render(mapping=mapping))

process_template('graph.dot.mako', 'sample_output.json')
