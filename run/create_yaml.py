import os
import sys
import string
import yaml
from argparse import ArgumentParser
import time

# default setting
traces = {}
realblobfiles = {}
limitamount = 5000
warmupthreads = 60 # number of total clients
hotratio = 0.25
nondedupreplicas = 2
replicalevel = 3
wait = True

dir = '/home/nannan/docker-performance/'
layerfiledir = '/home/nannan/dockerimages/layers/hulk1'

def createclientinfo(trace):
    client_info = {
        "threads": 1,
        "realblobs": os.path.join(layerfiledir, trace+'_layers.lst'),
            
            }
    return client_info

def createtrace(traces, limit):
    trace = {
        "location": "/home/nannan/dockerimages/docker-traces/data_centers",
        "traces": traces,
        "limit": {
            "amount": limit,
            },
        "output": "results.json",
        
        }
    return trace

def createwarmup(threads):
    warmup = {
        "output": "warmup_output.json",
        "threads": threads,
        } 
    return warmup
    
def createtestmode(testmode):
    nodedup = False
    sift = False
    restore = False
    
    if testmode == "nodedup":
        nodedup = True
    if testmode == "sift":
        sift = True
    if testmode == "restore":
        restore = True
    
    testmode = {
        "nodedup": nodedup,
        "sift": sift,
        "restore": restore,
        }
    
    return testmode

def createsiftparams(mode, hotratio, nondedupreplicas):
    siftparams = {
        "mode": mode,
        "selective":{
            "hotratio": hotratio,            
            },
        "standard":{
            "nondedupreplicas": nondedupreplicas,
            },
        }
    return siftparams

def createsimulate(wait, accelerater, replicalevel):
    simulate = {
        "wait": wait,
        "accelerater": accelerater,
        "replicalevel": replicalevel,
        }
    
    return simulate

"""
dal_layers.lst  fra_layers.lst  prestage_layers.lst  syd_layers.lst
dev_layers.lst  lon_layers.lst  stage_layers.lst     testing_layers.lst
"""

def main():
    #first add traces
    traces["dal"] = ["dal09/prod-dal09-logstash-2017.06.20-0.json"]
    traces["dev"] = ["dev-mon01/dev-mon01-logstash-2017.07.13-0.json", 
                     "dev-mon01/dev-mon01-logstash-2017.07.13-1.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.13-2.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.13-3.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.14-0.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.14-1.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.14-2.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.14-3.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.15-0.json",
                     "dev-mon01/dev-mon01-logstash-2017.07.15-1.json"]
    traces["fra"] = ["fra02/prod-fra02-logstash-2017.06.20-0.json",
                     "fra02/prod-fra02-logstash-2017.06.20-1.json",
                     "fra02/prod-fra02-logstash-2017.06.20-3.json",
                     "fra02/prod-fra02-logstash-2017.06.21-0.json",
                     "fra02/prod-fra02-logstash-2017.06.21-1.json",
                     "fra02/prod-fra02-logstash-2017.06.21-2.json",
                     "fra02/prod-fra02-logstash-2017.06.21-3.json",
                     "fra02/prod-fra02-logstash-2017.06.22-0.json",
                     "fra02/prod-fra02-logstash-2017.06.22-1.json",
                     "fra02/prod-fra02-logstash-2017.06.22-2.json",
                     "fra02/prod-fra02-logstash-2017.06.22-3.json"]
    traces["lon"] = ["lon02/prod-lon02-logstash-2017.06.20-0.json"]
    traces["prestage"] = ["prestage-mon01/prestage-mon01-logstash-2017.07.03-0.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.03-1.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.03-2.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.03-3.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.04-0.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.04-1.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.04-2.json",
                          "prestage-mon01/prestage-mon01-logstash-2017.07.04-3.json"]
    traces["stage"] = ["stage-dal09/stage-dal09-logstash-2017.06.27-0.json"]
    traces["syd"] = ["syd01/prod-syd01-logstash-2017.07.01-0.json",
                     "syd01/prod-syd01-logstash-2017.07.01-1.json",
                     "syd01/prod-syd01-logstash-2017.07.01-2.json",
                     "syd01/prod-syd01-logstash-2017.07.01-3.json",
                     "syd01/prod-syd01-logstash-2017.07.02-0.json",
                     "syd01/prod-syd01-logstash-2017.07.02-1.json",
                     "syd01/prod-syd01-logstash-2017.07.02-2.json",
                     "syd01/prod-syd01-logstash-2017.07.02-3.json"]
    
    registries=["192.168.0.200:5000",
                "192.168.0.201:5000",
                "192.168.0.202:5000",
                "192.168.0.203:5000",
                "192.168.0.204:5000",
                "192.168.0.205:5000",
                "192.168.0.208:5000",
                "192.168.0.209:5000",
                "192.168.0.210:5000",
                "192.168.0.211:5000",
                "192.168.0.212:5000",
                "192.168.0.213:5000",
                "192.168.0.214:5000",
                "192.168.0.215:5000",
                "192.168.0.216:5000",
                "192.168.0.217:5000",
                "192.168.0.218:5000",
                "192.168.0.219:5000",
                "192.168.0.221:5000",
                "192.168.0.222:5000",
                "192.168.0.223:5000"]
    
    clients = ["192.168.0.151",
               "192.168.0.153",
               "192.168.0.154",
               "192.168.0.156"]
    
    
    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
#     parser.add_argument('-r', '--realblobfiles', dest='realblobfiles', type=str, required=True, 
#                         help = 'input realblob files: 50m or 1gb')
    parser.add_argument('-t', '--tracefiles', dest='tracefiles', type=str, required=True, 
                        help = 'input trace file: dal, dev, fra, prestage, or syd, lon')
    parser.add_argument('-m', '--testmode', dest='testmode', type=str, required=True, 
                        help = 'input test mode: nodedup, sift, restore')
    parser.add_argument('-s', '--siftmode', dest='siftmode', type=str, required=True, 
                        help = 'input sift mode: standard, selective')
    parser.add_argument('-a', '--accelerater', dest='accelerater', type=int, required=True, 
                        help = 'input accelerater: int')
    parser.add_argument('-n', '--numofdedupregistries', dest='numofdedupregistries', type=int, required=True, 
                        help = 'input numofdedupregistries: int')
    parser.add_argument('-c', '--numofclients', dest='numofclients', type=int, required=True, 
                        help = 'input numofclients: int')
    
    args = parser.parse_args()
    print args
    client_info = createclientinfo(args.tracefiles)
    testingtrace = createtrace(traces[args.tracefiles], limitamount)

    primaryregistry=[]
    dedupregistry=[]

    testingclients = clients[:args.numofclients]
    warmup = createwarmup(warmupthreads)
    
    if args.testmode == "nodedup":
        primaryregistry = registries #registries(:,len(registries)-args.numofdedupregistries)
    elif args.testmode == "sift":
        dedupregistry = registries[:args.numofdedupregistries]
        primaryregistry = registries[-(len(registries)-args.numofdedupregistries):]
    elif args.testmode == "restore":
        dedupregistry = registries[:args.numofdedupregistries]
        
    testingmode = createtestmode(args.testmode)
    testingsiftmode = createsiftparams(args.siftmode, hotratio, nondedupreplicas)
    simulate = createsimulate(wait, args.accelerater, replicalevel)
    config = {
        "client_info": client_info,
        "trace": testingtrace,
        "primaryregistry": primaryregistry,
        "dedupregistry": dedupregistry,
        "clients": testingclients,
        "warmup": warmup,
        "testmode": testingmode,
        "siftparams": testingsiftmode,
        "simulate": simulate,
        }
    print config
    with open(os.path.join(dir, "config.yaml"), 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)
    with open(os.path.join(dir, "run/clients.txt"), 'w') as fp:
        for i in testingclients:
            fp.write(i+':22\n')
    with open(os.path.join(dir, "run/dedupregistries.txt"), 'w') as fp:
        for i in dedupregistry:
            tmp = i.split(':')[0]
            fp.write(tmp+':22\n')
    with open(os.path.join(dir, "run/primaryregistries.txt"), 'w') as fp:
        for i in primaryregistry:
            tmp = i.split(':')[0]
            fp.write(tmp+':22\n')

            
    
    
    
if __name__ == "__main__":
        main()
