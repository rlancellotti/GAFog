import org.omnetpp.queueing.Sink;

module Cloud
{
    parameters:
        @display("i=device/mainframe;is=l;p=$xpos,$ypos");
		double xpos = default(uniform(0, 500));
		double ypos = default(uniform(0, 500));
    gates:
        input in[];
    submodules:
        sink: Sink;
    connections:
        in[i] --> sink.in++ for i=0..sizeof(in)-1;
}

