import sys
import os
from argparse import ArgumentParser
import time
import datetime
import random
import json 
import yaml
from dxf import *
from collections import defaultdict
import socket
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from os.path import stat
from uhashring import HashRing
import numpy as np

from client import *
# from organize_requests import *
from split_into_clients import *

results_dir = "/home/nannan/testing/results/"

# TYPE XXX USRADDR XXX REPONAME XXX ; lowcases!!!!
"""
/*
//TYPE XXX USRADDR XXX REPONAME XXX
MANIFEST
LAYER
SLICE
PRECONSTRUCTLAYER
''''
WARMUPLAYER

*/
"""

def send_warmup_thread(req):
    registries = req[0]
    request = req[1]
    #print "send_warmup_thread"
    print("request: ", request)

    all = distribute_put_requests(request, 'WARMUP', registries)
    print("send_warmup_thread: ", all)
    return all 


#######################
# send to registries according to cht 
# warmup output file is <uri to dgst > map table
# only consider 'get' requests
# let set threads = n* len(registries)
#######################

def warmup(out_trace, threads):
    dedupL = {}
    dedupM = {}
    get_M = 0
    get_L = 0

    total_cnt = 0
    trace = {}
    results = []
    process_data = []
    
    fname = realblobtrace_dir+'input_tracefile'+'-client-realblob.json' 
    data = get_requests(fname)
    data.sort(key= lambda x: x['delay'])
    
    for request in data:
        unique = True

        if request['method'] == 'GET':
            uri = request['uri']
            id = uri.split('/')[-1]
            total_cnt += 1
            if 'manifest' in request['uri']:
                get_M += 1
                try:
                    x = dedupM[id]
                    continue
                except Exception as e:
                    dedupM[id] = 1
            else:
                get_L += 1
                try:
                    x = dedupL[id]
                    continue
                except Exception as e:
                    dedupL[id] = 1
            # *********** which registry should store this layer/manifest? ************  
            #uri = request['uri']
            if 'manifest' in uri:
                type = 'MANIFEST'
            else:
                type = 'WARMUPLAYER'
            parts = uri.split('/')
            reponame = parts[1] + parts[2]
            client = request['client']

            dedupreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
            nodedupreponame = "testrepo"
            registry_tmps = get_write_registries(request, dedupreponame, nodedupreponame)   
            print registry_tmps
            process_data.append((registry_tmps, request))

    n = 100
    process_slices = [process_data[i:i + n] for i in xrange(0, len(process_data), n)]
    #print threads
    for s in process_slices:
        with ProcessPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(send_warmup_thread, req) for req in s]
            for future in as_completed(futures):
#                 print(future.result())
                try:
                    x = future.result()
                    for k in x['trace']:
                        if x['trace'][k] != 'bad':
                            trace[k] = x['trace'][k]
                        
                    results.append(x['result'])    
                except Exception as e:
                    print('warmup: something generated an exception: %s', e)
        #break     
        #stats(results)
        #time.sleep(600)

    with open(out_trace, 'w') as f:
        json.dump(trace, f)
        
    stats(results)
    with open('warmup_push_performance.json', 'w') as f:
        json.dump(results, f)
    
    print "Warmup information:"
    print "Number of warmup threads: " + str(threads)
    print "Replica_level: " + str(replica_level)
    print 'Get layer request unique count: ' + str(len(dedupL))
    print 'Get manifest request unique count: ' + str(len(dedupM))
    
    print 'Total get layer request count: ' + str(get_L)
    print 'Total get manifest request count: ' + str(get_M)    
    print "Total warmup unique requests (for get layer/manifest requests): " + str(len(process_data))

#############
# NANNAN: change `onTime` for distributed dedup response
# {'size': size, 'onTime': onTime, 'duration': t}
# {'time': now, 'duration': t, 'onTime': onTime_l}
##############
 
def stats(responses):   
    if len(responses) == 0:
        return
    responses.sort(key = lambda x: x['time'])

    endtime = 0
    data = 0
    latency = 0
    total = len(responses)
    onTimes = 0
    failed = 0

    getlayerlatency = 0
    gettotallayer = 0
    getlayerlatencies = []

    getmanifestlatency = 0
    gettotalmanifest = 0
    getmanifestlatencies = []

    putlayerlatency = 0
    puttotallayer = 0
    putlayerlatencies = []

    putmanifestlatency = 0
    puttotalmanifest = 0
    putmanifestlatencies = []

    warmuplayerlatency = 0
    warmuptotallayer = 0
    warmuplayerlatencies = []

    warmupmanifestlatency = 0
    warmuptotalmanifest = 0 
    warmupmanifestlatencies = []   

    startTime = responses[0]['time']
    for r in responses:
        print r
        try:
            for i in r['onTime']:
                if "failed" in i['onTime']:
                    total -= 1
                    failed += 1
                    break # no need to care the rest partial layer.
                data += i['size']
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
        except Exception as e:
            if "failed" in r['onTime']:
                total -= 1
                failed += 1
                continue
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            data += r['size']
        
        if r['type'] == 'LAYER':
            getlayerlatency += r['duration']
            gettotallayer += 1
            getlayerlatencies.append(r['duration'])
            
        if r['type'] == 'MANIFEST':
            getmanifestlatency += r['duration']
            gettotalmanifest += 1
            getmanifestlatencies.append(r['duration'])
            
        if r['type'] == 'PUSHLAYER':
            putlayerlatency += r['duration']
            puttotallayer += 1
            putlayerlatencies.append(r['duration'])
            
        if r['type'] == 'PUSHMANIFEST':
            putmanifestlatency += r['duration']
            puttotalmanifest += 1
            putmanifestlatencies.append(r['duration'])
            
        if r['type'] == 'warmuplayer':
            warmuplayerlatency += r['duration']
            warmuptotallayer += 1
            warmuplayerlatencies.append(r['duration'])
            
        if r['type'] == 'warmupmanifest':
            warmupmanifestlatency += r['duration']
            warmuptotalmanifest += 1
            warmupmanifestlatencies.append(r['duration'])
                
    duration = endtime - startTime
    
    global accelerater
    global testmode
    
    print 'Statistics'
    print 'accelerater: '+str(accelerater)
    print 'testmode: ' + str(testmode)
    print 'Successful Requests: ' + str(total)
    print 'Failed Requests: ' + str(failed)
    print 'Duration: ' + str(duration)
    print 'Data Transfered: ' + str(data) + ' bytes'
    print 'Average Latency: ' + str(latency / total)
    print 'Throughput: ' + str(1.*total / duration) + ' requests/second'
    print 'Total GET layer: ' + str(gettotallayer)
    print 'Total GET manifest: ' + str(gettotalmanifest)
    print 'Total PUT layer: ' + str(puttotallayer)
    print 'Total PUT Manifest: ' + str(puttotalmanifest)
    print 'Total WAMRUP layer: ' + str(warmuptotallayer)
    print 'Total WAMRUP manifest: ' + str(warmuptotalmanifest)
    
    if gettotallayer > 0:
        print 'Average get layer latency: ' + str(1.*getlayerlatency/gettotallayer) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(getlayerlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(getlayerlatencies, 75))
        print("95th percentile of durations : ", np.percentile(getlayerlatencies, 95))
        print("99th percentile of durations : ", np.percentile(getlayerlatencies, 99))
        
    if puttotallayer > 0:
        print 'Average put layer latency: ' + str(1.*putlayerlatency/puttotallayer) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(putlayerlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(putlayerlatencies, 75))
        print("95th percentile of durations : ", np.percentile(putlayerlatencies, 95))
        print("99th percentile of durations : ", np.percentile(putlayerlatencies, 99))
               
    if gettotalmanifest > 0:
        print 'Average get manifest latency: ' + str(1.*getmanifestlatency/gettotalmanifest) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(getmanifestlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(getmanifestlatencies, 75))
        print("95th percentile of durations : ", np.percentile(getmanifestlatencies, 95))
        print("99th percentile of durations : ", np.percentile(getmanifestlatencies, 99))
        
    if puttotalmanifest > 0:
        print 'Average put manifest latency: ' + str(1.*putmanifestlatency/puttotalmanifest) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(putmanifestlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(putmanifestlatencies, 75))
        print("95th percentile of durations : ", np.percentile(putmanifestlatencies, 95))
        print("99th percentile of durations : ", np.percentile(putmanifestlatencies, 99))
        
    if warmuptotalmanifest > 0:
        print 'Average warmup manifest latency: ' + str(1.*warmupmanifestlatency/warmuptotalmanifest) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(warmupmanifestlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(warmupmanifestlatencies, 75))
        print("95th percentile of durations : ", np.percentile(warmupmanifestlatencies, 95))
        print("99th percentile of durations : ", np.percentile(warmupmanifestlatencies, 99))
        
    if warmuptotallayer > 0:
        print 'Average warmup layer latency: ' + str(1.*warmuplayerlatency/warmuptotallayer) + ' seconds/request'
        print("50th percentile of durations : ", np.percentile(warmuplayerlatencies, 50))  
        print("75th percentile of durations : ", np.percentile(warmuplayerlatencies, 75))
        print("95th percentile of durations : ", np.percentile(warmuplayerlatencies, 95))
        print("99th percentile of durations : ", np.percentile(warmuplayerlatencies, 99))

 
## send out requests to clients and get results
def get_blobs(data, numclients, out_file):#, testmode):
    results = []
    i = 0
    #""" # for debugging
    for reqlst in data:
	x = send_requests(reqlst)
	results.extend(x)
    #""" # end debugging
    """ # for run
    
    with ProcessPoolExecutor(max_workers = numclients) as executor:
        futures = [executor.submit(send_requests, reqlst) for reqlst in data]
        for future in as_completed(futures):
            try:
                x = future.result()
                results.extend(x)        
            except Exception as e:
                print('get_blobs: something generated an exception: %s', e)
        print "start stats"
    #stats(results)
    

    with open(results_dir+out_file, 'w') as f:
        json.dump(results, f)
    """ # end for run
    """ # for just extract result """
    with open(results_dir+out_file) as f:
        results = json.load(f)
    stats(results)
    """ # end for extracting"""

def main():

    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, 
                        help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, 
                        help = 'Trace player command. Possible commands: warmup, run, and simulate, \
                        warmup is used to populate the registry with the layers of the trace, \
                        run replays the trace, \
                        and simulate is not implemented yet.')

    args = parser.parse_args()
    config = file(args.input, 'r')
    global ring

    try:
        inputs = yaml.load(config)
    except Exception as inst:
        print 'error reading config file'
	print inst
        exit(-1)

    if 'trace' not in inputs:
        print 'trace field required in config file'
        exit(1)

    trace_files = []
    if 'location' in inputs['trace']:
        location = inputs['trace']['location']
        if '/' != location[-1]:
            location += '/'
        for fname in inputs['trace']['traces']:
            trace_files.append(location + fname) # actual trace file names
    else:
        trace_files.extend(inputs['trace']['traces']) # actual tfn

    print 'Input traces'
    for f in trace_files:
        print f

    limit = 0

    if 'limit' in inputs['trace']:
        limit = inputs['trace']['limit']['amount']
    else:
        print 'limit not set! please set replay request limit!'
        exit(1)

    if 'output' in inputs['trace']:
        out_file = inputs['trace']['output']
    else:
        out_file = 'output.json'
        print 'Output trace not specified, ./output.json will be used'
        
    if "warmup" not in inputs or 'output' not in inputs['warmup']:
        print 'warmup not specified in config, warmup output required. Exiting'
        exit(1)
    else:
        interm = inputs['warmup']['output']
    
    global primaryregistries    
    primaryregistries = []
    if 'primaryregistry' in inputs:
        primaryregistries.extend(inputs['primaryregistry'])
    print("primaryregistries: ", primaryregistries)
    
    global dedupregistries
    dedupregistries = []
    if 'dedupregistry' in inputs:
        dedupregistries.extend(inputs['dedupregistry'])
    print("dedupregistries: ", dedupregistries)
    
    global ring    
    ring = HashRing(nodes = primaryregistries)
    global ringdedup
    ringdedup = HashRing(nodes = dedupregistries) 
    
    clients = []
    if 'clients' in inputs:
        clients.extend(inputs['clients'])
    print(clients)
    
#    global gettype
#    gettype = inputs['simulate']['gettype']       
#    print("gettype layer or slice? ", gettype)
        
    wait = inputs['simulate']['wait']
    print ("wait or not? ", wait)
    
    global accelerater
    accelerater = inputs['simulate']['accelerater']
    print ("accelerater:  ", accelerater)
    
    global replica_level
    replica_level = inputs['simulate']['replicalevel']
    print ("replica_level:  ", replica_level)
       
    if 'threads' in inputs['warmup']:
        threads = inputs['warmup']['threads']
    else:
        threads = 1
    print 'warmup threads same as number of clients: ' + str(threads)

    global testmode
    global siftmod
    global hotratio
    global nondedupreplicas
    global hotlayers
    siftmode = 'N/A'
    hotratio = 0
    nondedupreplicas = 0


    if inputs['testmode']['nodedup'] == True:
        testmode = 'nodedup'
    elif inputs['testmode']['sift'] == True:
        testmode = 'sift' 
        siftmode = inputs['siftparams']['mode']
        print ("siftmode:  ", siftmode)
        if 'selective' == siftmode:
            hotratio = inputs['siftparams']['selective']['hotratio']
            print ("hotratio:  ", hotratio)
        elif 'standard' == siftmode:
            nondedupreplicas = inputs['siftparams']['standard']['nondedupreplicas']
            print ("nondedupreplicas:  ", nondedupreplicas)        
    elif inputs['testmode']['restore'] == True:
        testmode = 'restore'       
    
    if args.command == 'match':    
        if 'realblobs' in inputs['client_info']:
            realblob_locations = inputs['client_info']['realblobs'] 
            tracedata, layeridmap = fix_put_id(trace_files, limit)
            match(realblob_locations, tracedata, layeridmap)
            organize_and_send_clients(len(clients), clients, hotratio)
            return
	else:
	    print "please put realblobs in the config files"
	    return      
  
    fname = realblobtrace_dir+'input_tracefile'+'_hotlayers.json'
    with open(fname, 'r') as fp:
        hotlayers = json.load(fp)

    config_client(ring, ringdedup, dedupregistries, hotlayers, testmode, wait, accelerater, replica_level, siftmode, nondedupreplicas) 
        
    print("hot layers are: ", hotlayers)    
         
    if args.command == 'warmup': 
        print 'warmup mode'
        warmup(interm, threads/len(clients))

    elif args.command == 'run':
        print 'run mode'
        data = organize(interm, threads, clients)
        fname = out_file+'-'+socket.gethostname()
        get_blobs(data, threads/len(clients), fname)#, testmode)
    else:
        pass


if __name__ == "__main__":
    main()
