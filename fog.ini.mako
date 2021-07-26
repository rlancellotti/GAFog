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
**.source[${i}].interArrivalTime=exponential(${1/problem.lambda_src[i]}s)
**.source[${i}].xpos=${(problem.srcpos[i][0]-problem.xmin)/(problem.xmax-problem.xmin)}
**.source[${i}].ypos=${(problem.srcpos[i][1]-problem.ymin)/(problem.ymax-problem.ymin)}
%endfor
# infinite queue length
**.fog[*].capacity = -1
**.fog[*].fifo = true
%for i in range(problem.nfog):
**.fog[${i}].serviceTime=exponential(${1/problem.mu_fog[i]}s)
**.fog[${i}].xpos=${(problem.fogpos[i][0]-problem.xmin)/(problem.xmax-problem.xmin)}
**.fog[${i}].ypos=${(problem.fogpos[i][1]-problem.ymin)/(problem.ymax-problem.ymin)}
%endfor
**.sink.xpos=${(problem.fogpos[0][0]-problem.xmin)/(problem.xmax-problem.xmin)}
**.sink.ypos=${(problem.fogpos[0][1]-problem.ymin)/(problem.ymax-problem.ymin)}
