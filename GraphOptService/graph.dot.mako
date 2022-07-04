strict digraph {
    compound=true;
    subgraph cluster_logical {
        // service chains
        label="Service chains"
        style="dashed"
%for sc in mapping['servicechain']:
        subgraph cluster_${sc} {
            label="${sc}"
%for n, s in enumerate(mapping['servicechain'][sc]['services'].keys()):
%if n!= len(mapping['servicechain'][sc]['services'])-1:
          ${s} -> ${list(mapping['servicechain'][sc]['services'].keys())[n+1]}
%endif
%endfor

        }
%endfor
    }
    subgraph physical{
        subgraph cluster_fog {
            label="Fog nodes"
            style="dashed"
            node [shape=box] 
%for s in mapping['microservice']:
            ${mapping['microservice'][s]}
%endfor
        }
        subgraph cluster_sensor {
            style="dashed"
            label="Sensors"
            node [shape=circle] 
%for sc in mapping['servicechain']:
%for s in mapping['servicechain'][sc]['sensors']:
            ${s}
%endfor
%endfor
        }
    }
    // data flows
    subgraph {
        edge [color=blue]
%for sc in mapping['servicechain']:
%for s in mapping['servicechain'][sc]['sensors']:
            ${s} -> ${list(mapping['servicechain'][sc]['services'].keys())[0]}
%endfor
%endfor
    }
    // service mapping
    subgraph {
        edge [style=dashed, color=red]
%for m in mapping['microservice']:
        ${m} -> ${mapping['microservice'][m]}
%endfor
    }
    // sensor mapping
    subgraph {
        edge [style=dashed, color=orange]
%for s in mapping['sensor']:
        ${s} -> ${mapping['sensor'][s]}
%endfor
    }
}