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
%for i in range(problem.nsrc):
        source[${i}].out --> {delay = ${problem.dist_matrix[i][sol[i]]}s; } --> fog[${sol[i]}].in++;
%endfor
        // connect all fog nodes to sink
        for i=0..${problem.nfog-1} {
            fog[i].out --> sink.in++;
        }
}
