import org.omnetpp.queueing.Queue;

module FogNode
{
    parameters:
        @display("i=device/antennatower,$color,20;is=l;p=$xpos,$ypos");
		double xpos = default(uniform(0, 500));
		double ypos = default(uniform(0, 500));
        string color = default("black");
		volatile double serviceTime @unit(s) = default(1s);
		volatile int capacity = default(-1);
		server.serviceTime = serviceTime;
		server.capacity = capacity;
    gates:
        output out;
        input in[];
    submodules:
        server: Queue;
    connections:
        in[i] --> server.in++ for i=0..sizeof(in)-1;
        server.out --> out;
}

