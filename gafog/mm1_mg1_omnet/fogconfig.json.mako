<%
Prefix = "Fog"
%>
{
    "scenario_schema": {
        "Rho": {"pattern": "**.rho", "type": "real"},
        "DeltaMu": {"pattern": "**.deltamu", "type": "real"},
        "ServiceType": {"pattern": "**.servicetype", "type": "varchar(20)"}
    },
    "metrics": {
        "SentJobs": {"module": "**.source[*].source", "scalar_name": "created:last", "aggr": ["avg", "std", "sum"]},
        "SrvRho": {"module": "**.fog[*].server", "scalar_name": "busy:timeavg", "aggr": ["avg", "std"]},
        "SinkService": {"module": "**.sink", "scalar_name": "totalServiceTime:histogram/mean", "aggr": ["none"]},
        "SinkServiceStd": {"module": "**.sink", "scalar_name": "totalServiceTime:histogram/stddev", "aggr": ["none"]},
        "SinkDelay": {"module": "**.sink", "scalar_name": "totalDelayTime:histogram/mean", "aggr": ["none"]},
        "SinkDelayStd": {"module": "**.sink", "scalar_name": "totalDelayTime:histogram/stddev", "aggr": ["none"]},
        "SinkQueue": {"module": "**.sink", "scalar_name": "totalQueueingTime:histogram/mean", "aggr": ["none"]},
        "SinkQueueStd": {"module": "**.sink", "scalar_name": "totalQueueingTime:histogram/stddev", "aggr": ["none"]},
        "SinkTime": {"module": "**.sink", "scalar_name": "lifeTime:histogram/mean", "aggr": ["none"]},
        "SinkTimeStd": {"module": "**.sink", "scalar_name": "lifeTime:histogram/stddev", "aggr": ["none"]}
    },
    "histograms": {
        "SinkService": {"module": "**.sink", "histogram_name": "totalServiceTime:histogram"},
        "SinkDelay": {"module": "**.sink", "histogram_name": "totalDelayTime:histogram"},
        "SinkQueue": {"module": "**.sink", "histogram_name": "totalQueueingTime:histogram"},
        "SinkTime": {"module": "**.sink", "histogram_name": "lifeTime:histogram"}
    },
    "analyses": {
%for servicetype in ['exp', 'norm', 'lognormL', 'lognormM', 'lognormS']:
        "${Prefix}-${servicetype}": {
            "outfile": "analysis/${Prefix}-${servicetype}.data",
            "scenarios": {
                "fixed": {"ServiceType": "${servicetype}"},
                "range": ["Rho", "DeltaMu"]
            },
            "metrics": [
                {"metric": "SentJobs", "aggr": "sum"},
                {"metric": "SentJobs", "aggr": "avg"},
                {"metric": "SrvRho", "aggr": "avg"},
                {"metric": "SrvRho", "aggr": "std"},
                {"metric": "SinkService", "aggr": "none"},
                {"metric": "SinkServiceStd", "aggr": "none"},
                {"metric": "SinkDelay", "aggr": "none"},
                {"metric": "SinkDelayStd", "aggr": "none"},
                {"metric": "SinkQueue", "aggr": "none"},
                {"metric": "SinkQueueStd", "aggr": "none"},
                {"metric": "SinkTime", "aggr": "none"},
                {"metric": "SinkTimeStd", "aggr": "none"}
            ]
        },
%for hist in ['SinkService', 'SinkDelay', 'SinkQueue', 'SinkTime']:
        "${Prefix}-${servicetype}-${hist}H": {
            "outfile": "analysis/${Prefix}-${servicetype}-${hist}H.data",
            "scenario": {"ServiceType": "${servicetype}", "Rho": "0.5", "DeltaMu": "1"},
            "histogram": "${hist}"
        }\
%if loop.last and loop.parent.last:

%else:
,
%endif
%endfor
%endfor

    }
}