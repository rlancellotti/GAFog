import org.omnetpp.queueing.Delay;

module FogDelay
{
    parameters:
        @display("i=block/delay,$color,20;is=vs;p=$xpos,$ypos");
		double xpos = default(uniform(0, 500));
		double ypos = default(uniform(0, 500));
        string color = default("black");
		volatile double delay @unit(s); 
		internaldelay.delay = delay;
    gates:
        output out;
        input in[];
    submodules:
        internaldelay: Delay;
    connections:
        in[i] --> internaldelay.in++ for i=0..sizeof(in)-1;
        internaldelay.out --> out;
}

