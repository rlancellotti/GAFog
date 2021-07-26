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
%endfor
# infinite queue length
**.fog[*].capacity = -1
**.fog[*].fifo = true
%for i in range(problem.nfog):
**.fog[${i}].serviceTime=exponential(${1/problem.mu_fog[i]}s)
%endfor
