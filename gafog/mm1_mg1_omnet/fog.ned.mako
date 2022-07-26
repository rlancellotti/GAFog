import org.omnetpp.queueing.Cloud;
import org.omnetpp.queueing.FogNode;
import org.omnetpp.queueing.FogSensor;
import org.omnetpp.queueing.FogDelay;
<%
def get_color(n):
        return colors[n%len(colors)]
%>

network ${netname.capitalize()}
{
    parameters:
        @display("bgi=maps/fog,s;");
    submodules:
        sink: Cloud;
        fog[${problem.nfog}]: FogNode;
        source[${problem.nsrc}]: FogSensor;
        delay[${problem.nsrc}]: FogDelay;
    connections:
        // connect all sources to fog nodes
%for i in range(problem.nsrc):
        //source[${i}].out --> {delay = ${problem.dist_matrix[i][sol[i]]}s; @display("ls=${get_color(sol[i])}");} --> fog[${sol[i]}].in++;
        source[${i}].out --> {@display("ls=${get_color(sol[i])}");} --> delay[${i}].in++;
        delay[${i}].out --> {@display("ls=${get_color(sol[i])}");} --> fog[${sol[i]}].in++;
%endfor
        // connect all fog nodes to sink
%for i in range(problem.nfog):
        fog[${i}].out --> {@display("ls=${get_color(i)}");} --> sink.in++;
%endfor
}
