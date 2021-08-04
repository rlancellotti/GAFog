<%
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
**.delta = ${problem.delta}
**.nfog = ${problem.nfog}
%for i in range(problem.nsrc):
<%
    srcxpos, srcypos = get_coords(problem.srcpos[i])
    fogxpos, fogypos = get_coords(problem.fogpos[sol[i]])
    delayxpos=srcxpos*0.9+fogxpos*0.1
    delayypos=srcypos*0.9+fogypos*0.1
    color=get_color(sol[i])
%>\
**.source[${i}].interArrivalTime=exponential(${1/problem.lambda_src[i]}s)
**.source[${i}].xpos=${srcxpos}
**.source[${i}].ypos=${srcypos}
**.source[${i}].color="${color}"
**.delay[${i}].delay=1s * normal(${problem.dist_matrix[i][sol[i]]}, ${0.1*problem.dist_matrix[i][sol[i]]})
**.delay[${i}].xpos=${delayxpos}
**.delay[${i}].ypos=${delayypos}
**.delay[${i}].color="${color}"
%endfor
# infinite queue length
**.fog[*].capacity = -1
**.fog[*].fifo = true
%for i in range(problem.nfog):
<%
    fogxpos, fogypos = get_coords(problem.fogpos[i])
%>\
**.fog[${i}].serviceTime=exponential(${1/problem.mu_fog[i]}s)
**.fog[${i}].xpos=${fogxpos}
**.fog[${i}].ypos=${fogypos}
**.fog[${i}].color="${get_color(i)}"
%endfor
<%
    sinkxpos, sinkypos = get_coords(problem.sinkpos[0])
%>\
**.sink.xpos=${sinkxpos}
**.sink.ypos=${sinkypos}
