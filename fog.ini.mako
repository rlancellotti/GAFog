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
**.vector-recording = false
**.rho = ${problem.rho}
**.delta = ${problem.delta}
**.nfog = ${problem.nfog}
%for i in range(problem.nsrc):
<%
    srcxpos=(problem.xmax-problem.srcpos[i][0])/(problem.xmax-problem.xmin)
    srcypos=(problem.ymax-problem.srcpos[i][1])/(problem.ymax-problem.ymin)
    fogxpos=(problem.xmax-problem.fogpos[sol[i]][0])/(problem.xmax-problem.xmin)
    fogypos=(problem.ymax-problem.fogpos[sol[i]][1])/(problem.xmax-problem.xmin)
    delayxpos=srcxpos*0.9+fogxpos*0.1
    delayypos=srcypos*0.9+fogypos*0.1
%>\
**.source[${i}].interArrivalTime=exponential(${1/problem.lambda_src[i]}s)
**.source[${i}].xpos=${srcxpos}
**.source[${i}].ypos=${srcypos}
**.delay[${i}].delay=1s * normal(${problem.dist_matrix[i][sol[i]]}, ${0.1*problem.dist_matrix[i][sol[i]]})
**.delay[${i}].xpos=${delayxpos}
**.delay[${i}].ypos=${delayypos}
%endfor
# infinite queue length
**.fog[*].capacity = -1
**.fog[*].fifo = true
%for i in range(problem.nfog):
**.fog[${i}].serviceTime=exponential(${1/problem.mu_fog[i]}s)
**.fog[${i}].xpos=${(problem.xmax-problem.fogpos[i][0])/(problem.xmax-problem.xmin)}
**.fog[${i}].ypos=${(problem.ymax-problem.fogpos[i][1])/(problem.ymax-problem.ymin)}
%endfor
**.sink.xpos=${(problem.xmax-problem.fogpos[0][0])/(problem.xmax-problem.xmin)}
**.sink.ypos=${(problem.ymax-problem.fogpos[0][1])/(problem.ymax-problem.ymin)}
