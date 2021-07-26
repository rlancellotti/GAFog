import org.omnetpp.queueing.Cloud;
import org.omnetpp.queueing.FogNode;
import org.omnetpp.queueing.FogSensor;


network ${netname.capitalize()}
{
    parameters:
        @display("i=block/network2");
    submodules:
        sink: Cloud;
        fog[${problem.nfog}]: FogNode;
        source[${problem.nsrc}]: FogSensor;
    connections:
        // connect all sources to fog nodes
%for i in range(problem.nsrc):
        source[${i}].out --> {delay = ${problem.dist_matrix[i][sol[i]]}s; @display("ls=${colors[sol[i]%len(colors)]}");} --> fog[${sol[i]}].in++;
%endfor
        // connect all fog nodes to sink
%for i in range(problem.nfog):
        fog[${i}].out --> {@display("ls=${colors[i%len(colors)]}");} --> sink.in++;
%endfor
}
