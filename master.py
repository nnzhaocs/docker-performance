import sys
#import socket
import os
from argparse import ArgumentParser
#import requests
import time
import datetime
#import pdb
import random
#import threading
#import multiprocessing
import json 
import yaml
from dxf import *
#from multiprocessing import Process, Queue
#import importlib
#import hash_ring
from collections import defaultdict

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from client import *
from os.path import stat
from uhashring import HashRing

def send_warmup_thread(req):
    registry = req[0]
    request = req[1]
    all = {}
    trace = {}
    size = 0
    onTime = 'yes'
    now = time.time()
    #print "================== req:"
    #print request
    full_uri = request['uri']
    #print full_uri
    uri_trunks = full_uri.split('/')
    uri = uri_trunks[1] + uri_trunks[2]
    dxf = DXF(registry, uri, insecure=True) #DXF(registry, 'test_repo', insecure=True)
    #for request in requests:
    try:
        dgst = dxf.push_blob(request['data'])
    except Exception as e:
        print("dxf send exception: ", e, request['data'])
        dgst = 'bad'
        onTime = 'failed: '+str(e)
        
    t = time.time() - now
    result = {'time': now, 'size': request['size'], 'onTime': onTime, 'duration': t, 'type': 'warmup'}
    #print("Putting results for: ", dgst, result)
#     return result
    print result
    print request['uri'], dgst
    trace[request['uri']] = dgst
    all = {'trace': trace, 'result': result}
    return all

#######################
# send to registries according to cht 
# warmup output file is <uri to dgst > map table
# only consider 'get' requests
# let set threads = n* len(registries)
#######################

def warmup(data, out_trace, registries, threads):
    trace = {}
    results = []
    process_data = []
    global ring
    ring = HashRing(nodes = registries)
       
    for request in data:
        if (request['method']) == 'GET':# and ('blobs' in request['uri']):
            uri = request['uri']
            layer_id = uri.split('/')[-1]
            registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
            #idx = registries.index(registry_tmp) 
            process_data.append((registry_tmp, request))
#     print process_data
    print("total requests:", len(process_data))
    #n = len(process_data)
    n = 100
    process_slices = [process_data[i:i + n] for i in xrange(0, len(process_data), n)]
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
                    print('something generated an exception: %s', e)
	#break     
        stats(results)
	#time.sleep(600)

    with open(out_trace, 'w') as f:
        json.dump(trace, f)
        
    stats(results)
    with open('warmup_push_performance.json', 'w') as f:
        json.dump(results, f)
            
    print("max threads:", threads)

# def getResFromRedis(filename):


#############
# NANNAN: change `onTime` for distributed dedup response
# {'size': size, 'onTime': onTime, 'duration': t}
# {'time': now, 'duration': t, 'onTime': onTime_l}
##############
 
def stats(responses):
    responses.sort(key = lambda x: x['time'])

    endtime = 0
    data = 0
    latency = 0
    total = len(responses)
    onTimes = 0
    failed = 0
    layerlatency = 0
    totallayer = 0

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
        
        if r['type'] == 'layer':
            layerlatency += r['duration']
            totallayer += 1

            
    duration = endtime - startTime
    print 'Statistics'
    print 'Successful Requests: ' + str(total)
    print 'Failed Requests: ' + str(failed)
    print 'Duration: ' + str(duration)
    print 'Data Transfered: ' + str(data) + ' bytes'
    print 'Average Latency: ' + str(latency / total)
    print 'Throughput: ' + str(1.*total / duration) + ' requests/second'
    if totallayer > 0:
        print 'Average layer latency: ' + str(1.*layerlatency/totallayer)

 
## Get blobs
def get_blobs(data, numclients, out_file):#, testmode):
    results = []
    i = 0
    #n = 100
    #process_slices = [data[i:i + n] for i in xrange(0, len(data), n)]
    #for s in process_slices:
    with ProcessPoolExecutor(max_workers = numclients) as executor:
        futures = [executor.submit(send_requests, reqlst) for reqlst in data]
        for future in as_completed(futures):
	    #print i
	    #i += 1
            #print future.result()
            try:
                x = future.result()
                results.extend(x)        
            except Exception as e:
                print('get_blobs: something generated an exception: %s', e)
        print "start stats"
        stats(results)
	#time.sleep(60*2)
    with open(out_file, 'w') as f:
        json.dump(results, f)
       

######
# NANNAN: trace_file+'-realblob.json'
######
def get_requests(files, t, limit):
    ret = []
    requests = []
    for filename in files:
        with open(filename+'-realblob.json', 'r') as f:
            requests.extend(json.load(f))
    
        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):
                size = request['http.response.written']
                if size > 0:
                    timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    duration = request['http.request.duration']
                    client = request['http.request.remoteaddr']
                    blob = request['data']
                    r = {
                        'delay': timestamp, 
                        'uri': uri, 
                        'size': size, 
                        'method': method, 
                        'duration': duration,
                        'client': client,
                        'data': blob
                    }
                    ret.append(r)
    ret.sort(key= lambda x: x['delay'])
    begin = ret[0]['delay']

    for r in ret:
        r['delay'] = (r['delay'] - begin).total_seconds()
   
    if t == 'seconds':
        begin = ret[0]['delay']
        i = 0
        for r in ret:
            if r['delay'] > limit:
                break
            i += 1
        print i 
        return ret[:i]
    elif t == 'requests':
        return ret[:limit]
    else:
        return ret


####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####

def match(realblob_location_files, trace_files, limit):
    print realblob_location_files, trace_files

    blob_locations = []
    tTOblobdic = {}
    blobTOtdic = {}
    ret = []
    i = 0
    count = 0
    for realblob_location_file in realblob_location_files:
    	print "File: "+realblob_location_file+" has the following blobs"
    
    	with open(realblob_location_file, 'r') as f:
            for line in f:
            	print line
            	if line:
                    blob_locations.append(line.replace("\n", ""))
    
    for trace_file in trace_files:
        with open(trace_file, 'r') as f:
            requests = json.load(f)
            
        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']
            if len(uri.split('/')) < 3:
                continue
            
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):# we only map layers not manifest; ('manifest' in uri) or 
                layer_id = uri.rsplit('/', 1)[1]
                size = request['http.response.written']
                if size > 0:
                    if count > limit:
                        break
                    if i < len(blob_locations):
                        if 'manifest' in uri:
                            blob = './config_1.yaml'
                        else:
                            blob = blob_locations[i]
                            i += 1
                            if layer_id in tTOblobdic.keys():
                                continue
                            if blob in blobTOtdic.keys():
                                print "this is not gonna happen"
                                continue
                            
                            tTOblobdic[layer_id] = blob
                            blobTOtdic[blob] = layer_id
    
                            size = os.stat(blob).st_size
                
                        r = {
                            "host": request['host'],
                            "http.request.duration": request['http.request.duration'],
                            "http.request.method": request['http.request.method'],
                            "http.request.remoteaddr": request['http.request.remoteaddr'],
                            "http.request.uri": request['http.request.uri'],
                            "http.request.useragent": request['http.request.useragent'],
                            "http.response.status": request['http.response.status'],
                            "http.response.written": size,
                            "id": request['id'],
                            "timestamp": request['timestamp'],
                            'data': blob
                        }
                        print r
                        ret.append(r)
                        count += 1
                               
        with open(trace_file+'-realblob.json', 'w') as fp:
            json.dump(ret, fp)      
        
##############
# NANNAN: round_robin is false!
# "http.request.duration": 1.005269323, 
# "http.request.uri": "v2/4715bf52/437c49db/blobs/93054319", 
# "host": "dc118836", 
# "http.request.useragent": "docker/17.03.1-ce go/go1.7.5 git-commit/c6d412e kernel/4.4.0-78-generic os/linux arch/amd64 UpstreamClient(Docker-Client/17.03.1-ce \\(linux\\))", 
# "timestamp": "2017-06-20T02:41:18.399Z", 
# "id": "ed29d65dbd", 
# "http.response.written": 9576, 
# "http.response.status": 200, 
# "http.request.method": "GET", 
# "http.request.remoteaddr": "0ee76ffa"
##############

def organize(requests, out_trace, numclients):
    organized = [[] for x in xrange(numclients)]
    clientTOThreads = {}
    clientToReqs = defaultdict(list)
    
    with open(out_trace, 'r') as f:
        blob = json.load(f)
            
    for r in requests:
        request = {
            'delay': r['delay'],
            'duration': r['duration'],
            'data': r['data'],
            'uri': r['uri'],
	    'client': r['client']
        }
        if r['uri'] in blob:
            b = blob[r['uri']]
            if b != 'bad':
                request['blob'] = b # dgest
                request['method'] = 'GET'
        else:
            request['size'] = r['size']
            request['method'] = 'PUT'
            
        clientToReqs[r['client']].append(request)
                
    img_req_group = []
    for cli, reqs in clientToReqs.items():
        cli_img_req_group = [[]]
        cli_img_push_group = [[]]
        prev = cli_img_req_group[-1]
        prev_push = cli_img_push_group[-1]
        
        for req in reqs:
            uri = req['uri']
            if req['method'] == 'GET':
                #print 'GET: '+uri
                if 'blobs' in uri:
                    #print 'GET layer:'+uri
                    prev.append(req)
                else:
                    #print 'GET manifest:'+uri
                    cur = []
                    cur.append(req)
                    cli_img_req_group.append(cur)
                    prev = cli_img_req_group[-1]
            else:
                #print 'PUT: '+uri
                if 'blobs' in uri:
                    #print 'PUT layer:'+uri
                    prev_push.append(req)
                elif 'manifests' in uri:
                    #print 'PUT manifest:'+uri
                    prev_push.append(req)
                    cur_push = []
                    cli_img_push_group.append(cur_push)
                    prev_push = cli_img_push_group[-1]
        
        cli_img_req_group += cli_img_push_group
        cli_img_req_group_new = [x for x in cli_img_req_group if len(x)]
        #print cli_img_req_group_new
        img_req_group += cli_img_req_group_new
        img_req_group.sort(key= lambda x: x[0]['delay'])

#     with open(input_dir + fname + '-sorted_reqs_repo_client.lst', 'w') as fp:
#         json.dump(img_req_group, fp)
    
    i = 0
    for r in img_req_group:
        req = r[0]
        try:
            threadid = clientTOThreads[req['client']]
            organized[threadid].append(r)
        except Exception as e:
            organized[i%numclients].append(r)
            clientTOThreads[req['client']] = i%numclients
            i += 1     
    print ("number of clients: %s", i)       
#         print req

    return organized


def main():

    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    parser.add_argument('-p', '--port', dest='pppp', type=str, required=False, help = 'identifier')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, help= 'Trace player command. Possible commands: warmup, run, simulate, warmup is used to populate the registry with the layers of the trace, run replays the trace, and simulate is used to test different caching and prefecting policies.')

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
            trace_files.append(location + fname)
    else:
        trace_files.extend(inputs['trace']['traces'])

    print 'Input traces'
    for f in trace_files:
        print f

    limit_type = None
    limit = 0

    if 'limit' in inputs['trace']:
        limit_type = inputs['trace']['limit']['type']
        if limit_type in ['seconds', 'requests']:
            limit = inputs['trace']['limit']['amount']
        else:
            print 'Invalid trace limit_type: limit_type must be either seconds or requests'
            exit(1)
    else:
        print 'limit_type not specified, entirety of trace files will be used will be used.'

    if 'output' in inputs['trace']:
        out_file = inputs['trace']['output']
    else:
        out_file = 'output.json'
        print 'Output trace not specified, ./output.json will be used'

    if args.command != 'simulate':
        if "warmup" not in inputs or 'output' not in inputs['warmup']:
            print 'warmup not specified in config, warmup output required. Exiting'
            exit(1)
        else:
            interm = inputs['warmup']['output']

    registries = []
    if 'registry' in inputs:
        registries.extend(inputs['registry'])
     
    print(registries)
    #NANNAN
    if args.command == 'match':    
        if 'realblobs' in inputs['client_info']:
            realblob_locations = inputs['client_info']['realblobs']
            match(realblob_locations, trace_files, limit)
            return
	else:
	    print "please write realblobs in the config files"
	    return

    json_data = get_requests(trace_files, limit_type, limit)

    if 'threads' in inputs['warmup']:
        threads = inputs['warmup']['threads']
    else:
        threads = 1
    print 'warmup threads same as number of clients: ' + str(threads)
    
    if inputs['testmode']['nodedup'] == True:
        testmode = 'nodedup'
    elif inputs['testmode']['traditionaldedup'] == True:
        testmode = 'traditionaldedup'
    else:
        testmode = 'sift'    

    if 'threads' not in inputs['client_info']:
        print 'client threads not specified, 1 thread will be used'
        client_threads = 1
    else:
        client_threads = inputs['client_info']['threads']
        print str(client_threads) + ' client threads'

    config_client(client_threads, registries, testmode) #requests, out_trace, numclients   
         
    if args.command == 'warmup': 
        print 'warmup mode'
        # NANNAN: not sure why only warmup a single registry, let's warmup all.
        warmup(json_data, interm, registries, threads)

    elif args.command == 'run':
        print 'run mode'
        data = organize(json_data, interm, threads)
        ## Perform GET
        get_blobs(data, threads, out_file)#, testmode)


    elif args.command == 'simulate':
        if verbose:
            print 'simulate mode'
        if 'simulate' not in inputs:
            print 'simulate file required in config'
            exit(1)
        pi = inputs['simulate']['name']
        if '.py' in pi:
            pi = pi[:-3]
        try:
            plugin = importlib.import_module(pi)
        except Exception as inst:
            print 'Plugin did not work!'
            print inst
            exit(1)
        try:
            if 'args' in inputs['simulate']:
                plugin.init(json_data, inputs['simulate']['args'])
            else:
                plugin.init(json_data)
        except Exception as inst:
            print 'Error running plugin init!'
            print inst


if __name__ == "__main__":
    main()
