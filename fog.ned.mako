//
// This file is part of an OMNeT++/OMNEST simulation example.
//
// Copyright (C) 2006-2015 OpenSim Ltd
//
// This file is distributed WITHOUT ANY WARRANTY. See the file
// `license' for details on this and other legal matters.
//

import org.omnetpp.queueing.Queue;
import org.omnetpp.queueing.Sink;
import org.omnetpp.queueing.Source;


//
// This simple queueing network only contains a source, a FIFO queue and a sink.
//
network Fog
{
    parameters:
        @display("i=block/network2");
    submodules:
        sink: Sink
        fog: Queue[${problem.nfog}]
        source: Source[${problem.nsrc}]
    connections:
%for i in range(problem.nsrc):
    source[${i}].out --> fog[${sol[i]}].in++;
%endfor
    // connect all fog nodes to sink
    for i in 0..${problem.nfog}{
        fog[i].out --> sink.in++;
    }
}
