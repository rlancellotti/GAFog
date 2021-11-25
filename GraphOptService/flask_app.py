from flask import Flask, request, Response
import json
from dot import process_template, render_image

app = Flask(__name__)
# Flask API
# submitting jobs
ftemplate = 'graph.dot.mako'

@app.post("/api/v1.0/graph.dot")
def make_dot():
    if request.is_json:
        data = request.get_json()
        out = process_template(ftemplate, data)
        return Response(out, mimetype='text/x-dot')
    return {'message': 'Request must be JSON'}, 415

@app.post("/api/v1.0/graph.svg")
def make_svf():
    if request.is_json:
        data = request.get_json()
        out = render_image(process_template(ftemplate, data))
        return Response(out, mimetype='image/svg+xml')
    return {'message': 'Request must be JSON'}, 415

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)