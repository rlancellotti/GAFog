#!/usr/bin/python3
from typing import Text
from mako.template import Template
from mako.runtime import Context
import json
import subprocess

def get_filename(ftemplate):
    return ftemplate.replace('.mako', '')

def process_template(ftemplate, sol):
    mytemplate=Template(filename=ftemplate)
    return mytemplate.render(mapping=sol)

def render_image(dotcode):
    #subprocess.run(['dot', dotfile, '-Tsvg', '-O'])
    p = subprocess.run(['dot', '-Tsvg'], input=dotcode, capture_output=True, text=True)
    return p.stdout

if __name__ == '__main__':
    fdata = 'sample_output.json'
    ftemplate = 'graph.dot.mako'
    with open(fdata, 'r') as f:
        data = json.load(f)
    out = process_template(ftemplate, data)
    fout = get_filename(ftemplate)
    with open(fout, 'w') as f:
        f.write(out)
    render_image(out)