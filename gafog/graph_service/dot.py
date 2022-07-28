#!/usr/bin/python3
from mako.template import Template
import argparse
import json
import subprocess
import pathlib


def get_filename(ftemplate):
    return ftemplate.replace('.mako', '')

def process_template(ftemplate, sol):
    mytemplate = Template(filename=ftemplate)
    return mytemplate.render(mapping=sol)


def render_image(dotcode, outtype="svg"):
    # subprocess.run(['dot', dotfile, '-Tsvg', '-O'])
    p = subprocess.run(['dot', '-T%s'%outtype], input=bytearray(dotcode.encode()), capture_output=True)
    return p.stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='output file. Default graph.svg')
    parser.add_argument('-f', '--file', help='input file. Default use sample_output.json')
    args = parser.parse_args()
    fdata = args.file or "gafog/graph_service/sample_output.json"
    ftemplate = "gafog/graph_service/graph.dot.mako"
    with open(fdata, "r") as f:
        data = json.load(f)
    out = process_template(ftemplate, data)
    fout = args.output or "sample/graph.svg"
    if fout.endswith('.dot'):
        with open(fout, 'w') as f:
            f.write(out)
    else:
        outtype = pathlib.Path(fout).suffix.strip('.')
        with open(fout, 'wb') as f:
            f.write(render_image(out, outtype))
