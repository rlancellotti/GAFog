<%
step=2
nfog=len(mapping['fog'])
nsc=len(mapping['servicechain'])
nsens=len(mapping['sensor'])
height=max(nfog, nsc, nsens)
maxms=max(len(mapping['servicechain'][sc]['services']) for sc in mapping['servicechain'])
width=maxms+1
xmin={'sensor': 0, 'service':1, 'fog': width}
ymin={'sensor': (height-nsens)/2, 'service':(height-nsc)/2, 'fog': (height-nsens)/2}
def get_xpos(grp, n):
    return (xmin[grp]+n)*step

def get_ypos(grp, n):
    return (ymin[grp]+n)*step

%>

strict digraph {
    compound=true;
    subgraph cluster_logical {
        // service chains
        label="Service chains"
        style="dashed"
%for nc, sc in enumerate(mapping['servicechain']):
        subgraph cluster_${sc} {
            label="${sc}"
%for ns, s in enumerate(mapping['servicechain'][sc]['services'].keys()):
            ${s} [pos="${get_xpos('service', ns)}, ${get_ypos('service', nc)}!"]
%endfor
            \
%for s in mapping['servicechain'][sc]['services'].keys():
${s} \
%if not loop.last: 
-> \
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
%for nf, f in enumerate(mapping['fog']):
            ${f} [pos="${get_xpos('fog', 0)}, ${get_ypos('fog', nf)}!"]
%endfor
            \
%for f in mapping['fog'].keys():
${f} \
%if loop.last:
[ style=invis ]
%else:
-> \
%endif
%endfor
        }
        subgraph cluster_sensor {
            style="dashed"
            label="Sensors"
            node [shape=circle]
%for ns, f in enumerate(mapping['sensor']):
            ${f} [pos="${get_xpos('sensor', 0)}, ${get_ypos('sensor', ns)}!"]
%endfor
            \
%for s in mapping['sensor']:
${s} \
%if loop.last:
[ style=invis ]
%else:
-> \
%endif
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