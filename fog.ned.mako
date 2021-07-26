import org.omnetpp.queueing.Queue;
import org.omnetpp.queueing.Sink;
import org.omnetpp.queueing.Source;


network ${netname.capitalize()}
{
    parameters:
        @display("i=block/network2");
    submodules:
        sink: Sink;
        fog[${problem.nfog}]: Queue;
        source[${problem.nsrc}]: Source;
    connections:
%for i in range(problem.nsrc):
        source[${i}].out --> fog[${sol[i]}].in++;
%endfor
        // connect all fog nodes to sink
        for i=0..${problem.nfog-1} {
            fog[i].out --> sink.in++;
        }
}
