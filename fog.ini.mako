<%
import numpy as np
def get_coords(point):
    x=(point[0]-problem.xmin)/(problem.xmax-problem.xmin)
    y=(problem.ymax-point[1])/(problem.ymax-problem.ymin)
    return x, y

def get_color(n):
    return colors[n%len(colors)]
%>
[General]
network = ${netname.capitalize()}
ned-path = .;../queueinglib
#cpu-time-limit = 60s
cmdenv-config-name = FogBase
qtenv-default-config = FogBase
repeat = 5
sim-time-limit = 900s
#debug-on-errors = true
# parameters of the simulation

[Config FogBase]
description = "Global scenario"
# results collection
**.vector-recording = false
**.sink.totalServiceTime.result-recording-modes = default,-vector,+histogram
**.sink.totalQueueingTime.result-recording-modes = default,-vector,+histogram
**.sink.totalDelayTime.result-recording-modes = default,-vector,+histogram
**.sink.lifeTime.result-recording-modes = default,-vector,+histogram
**.fog[*].server.busy.result-recording-modes = default,-vector

**.rho = ${problem.rho}
**.deltamu = ${problem.delta*np.mean(problem.mu_fog)}
**.expectedprocessing = ${ga['expected_processing']}
**.expecteddelay = ${ga['expected_delay']}
**.nfog = ${problem.nfog}
%for i in range(problem.nsrc):
<%
    srcxpos, srcypos = get_coords(problem.srcpos[i])
    fogxpos, fogypos = get_coords(problem.fogpos[sol[i]])
    delayxpos=srcxpos*0.9+fogxpos*0.1
    delayypos=srcypos*0.9+fogypos*0.1
    color=get_color(sol[i])
%>\
**.source[${i}].xpos=${srcxpos}
**.source[${i}].ypos=${srcypos}
**.source[${i}].color="${color}"
**.source[${i}].interArrivalTime=exponential(${1/problem.lambda_src[i]}s)
**.delay[${i}].xpos=${delayxpos}
**.delay[${i}].ypos=${delayypos}
**.delay[${i}].color="${color}"
**.delay[${i}].delay=1s * normal(${problem.dist_matrix[i][sol[i]]}, ${0.1*problem.dist_matrix[i][sol[i]]})
%endfor
# infinite queue length
**.fog[*].capacity = -1
**.fog[*].fifo = true
%for i in range(problem.nfog):
<%
    fogxpos, fogypos = get_coords(problem.fogpos[i])
%>\
**.fog[${i}].xpos=${fogxpos}
**.fog[${i}].ypos=${fogypos}
**.fog[${i}].color="${get_color(i)}"
%endfor
<%
    sinkxpos, sinkypos = get_coords(problem.sinkpos[0])
%>\
**.sink.xpos=${sinkxpos}
**.sink.ypos=${sinkypos}

# LOGNORMAL VERSION
# Lognormal parameters: m, w
# We want a distribution with paremters mean=mu, stddev=sigma
# note: mu (mean) is not mu (processing rate)!
# m=ln(mu^2/sqrt(mu^2+sigma^2))
# w^2=ln(1+(sigma^2/mu^2))
# we want sigma=4*mu
# m=ln(mu/sqrt(1+16))
# w^2=ln(1+16)
# We consider:
# lognormL: sigma=1.5 mu
# lognormM: sigma=mu
# lognormS: sigma=0.5 mu

%for distr in ['exp', 'norm', 'lognormL', 'lognormM', 'lognormS']:
[Config Fog${distr}]
extends=FogBase
**.servicetype = "${distr}"
%for i in range(problem.nfog):
%if distr=='exp':
**.fog[${i}].serviceTime=exponential(${1/problem.mu_fog[i]}s)
%elif distr=='norm':
**.fog[${i}].serviceTime=1s * truncnormal(${1/problem.mu_fog[i]}, ${0.1/problem.mu_fog[i]})
%elif distr=='lognormL':
**.fog[${i}].serviceTime=1s * lognormal(log(${1/problem.mu_fog[i]}/sqrt(3.25)), sqrt(log(3.25)))
%elif distr=='lognormM':
**.fog[${i}].serviceTime=1s * lognormal(log(${1/problem.mu_fog[i]}/sqrt(2)), sqrt(log(2)))
%elif distr=='lognormS':
**.fog[${i}].serviceTime=1s * lognormal(log(${1/problem.mu_fog[i]}/sqrt(1.25)), sqrt(log(1.25)))
%endif
%endfor

%endfor
