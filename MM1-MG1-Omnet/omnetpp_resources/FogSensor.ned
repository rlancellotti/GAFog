import org.omnetpp.queueing.Source;

module FogSensor
{
    parameters:
        @display("i=device/accesspoint,$color,20;is=s;p=$xpos,$ypos");
		double xpos = default(uniform(0, 500));
		double ypos = default(uniform(0, 500));
        string color = default("black");
		volatile double interArrivalTime @unit(s) = default(1s);
		source.interArrivalTime = interArrivalTime;
    gates:
        output out;
    submodules:
        source: Source;
    connections:
        source.out --> out;
}

