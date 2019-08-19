import traceback

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
from organize_requests import *
from os.path import stat
from uhashring import HashRing


#realblobtrace_dir = "/home/nannan/testing/realblobtraces/"
results_dir = "/home/nannan/testing/results/"

# TYPE XXX USRADDR XXX REPONAME XXX ; lowcases!!!!
"""
/*
//TYPE XXX USRADDR XXX REPONAME XXX
MANIFEST
LAYER
SLICE
PRECONSTRUCTLAYER
*/
"""

def send_warmup_thread(req):
    registry = req[0]
    request = req[1]

    all = {}
    trace = {}
    size = request['size']
    onTime = 'yes'

    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    
    newreponame = ''
    client = request['client']
    
    if 'manifest' in uri:
        type = 'MANIFEST'
    else:
        type = 'LAYER'
    
    newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
    #print("newreponame: ", newreponame)   
    dxf = DXF(registry, newreponame.lower(), insecure=True) 
    
    blobfname = ''
    # manifest: randomly generate some files
    if not request['data']:
        with open(str(os.getpid()), 'wb') as f: 
            f.write(str(random.getrandbits(64)))
            f.write('\n')
        blobfname = str(os.getpid())
    else:
        blobfname = request['data']

    now = time.time()
    try:                     
        dgst = dxf.push_blob(blobfname)
    except Exception as e:
        print("dxf send exception: ", e, request['data'])
        dgst = 'bad'
        onTime = 'failed: '+str(e)
        
    t = time.time() - now
    result = {'time': now, 'size': request['size'], 'onTime': onTime, 'duration': t, 'type': 'warmup'}
    print result
    
    clear_extracting_dir(str(os.getpid()))

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
    dedup = {}
#     dup_cnt = 0
    total_cnt = 0
    trace = {}
    results = []
    process_data = []
    global ring
    ring = HashRing(nodes = registries)
    manifs_cnt = 0

    for request in data:
        unique = True
	manifs = False
        if (request['method']) == 'GET':
	    if 'manifest' in request['uri']:
		manifs = True
            uri = request['uri']
            layer_id = uri.split('/')[-1]
            total_cnt += 1
            try:
                dup_cnt = dedup[layer_id]
#                 dup_cnt += 1
#                 dedup[layer_id] += 1
                unique = False
            except Exception as e:
                dedup[layer_id] = 1
		if manifs:
		    manifs_cnt += 1
                
            if unique:
                registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
                process_data.append((registry_tmp, request))

    print("total warmup unique requests:", len(process_data))
    print("unique manifest cnt: ", manifs_cnt)
    #split request list into sublists
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
                    print('warmup: something generated an exception: %s', e)
        #break     
        stats(results)
        #time.sleep(600)

    with open(out_trace, 'w') as f:
        json.dump(trace, f)
        
    stats(results)
    with open('warmup_push_performance.json', 'w') as f:
        json.dump(results, f)
    
    print "max threads:" + str(threads)
    print 'unique count: ' + str(len(dedup))
    print 'total count: ' + str(total_cnt)
    print "total warmup unique requests: (for get layer/manifest requests)" + str(len(process_data))


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
        
        if r['type'] == 'LAYER' or r['type'] == 'SLICE':
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
        print 'Average layer latency: ' + str(1.*layerlatency/totallayer) + ' seconds/request'

 
## send out requests to clients and get results
def get_blobs(data, numclients, out_file):#, testmode):
    results = []
    i = 0
    """ # for debugging
    for reqlst in data:
	x = send_requests(reqlst)
	results.extend(x)
    """
    #""" # for run
    with ProcessPoolExecutor(max_workers = numclients) as executor:
        futures = [executor.submit(send_requests, reqlst) for reqlst in data]
        for future in as_completed(futures):
            try:
                x = future.result()
                results.extend(x)        
            except Exception as e:
                print('get_blobs: something generated an exception: %s', e)
        print "start stats"
        stats(results)
    #"""

    with open(results_dir+out_file, 'w') as f:
        json.dump(results, f)
       

##############
# NANNAN: add a sleep delay
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
#assume numclients is always power of 2
'''def bi_load_balance(numclients, client_reqCount, clientToReqs):
    # source: https://www.geeksforgeeks.org/partition-a-set-into-two-subsets-such-that-the-difference-of-subset-sums-is-minimum/
    print 'num O clients: ' + str(numclients)
    print 'client req count: ' + str(client_reqCount)
    def split_req(c_rCount):
        results = [[],[]]
        #reqCnt = [x[1] for x in c_rCount]
        #print c_rCount[0]
        #print reqCnt[0]
        summed = sum([x[1] for x in c_rCount])
        n = len(c_rCount)
        dp =[[[False, []] for i in range(summed + 1)] for j in xrange(n + 1)]
        
        for row in dp:
            row[0][0] = True
        
        for i in range(n + 1):
            for j in range(summed + 1):
                
                dp[i][j][0] = dp[i - 1][j][0]
                if dp[i - 1][j][0]:
                    dp[i][j][1].extend(dp[i - 1][j][1])
                    #print 'i - 1:'
                    #print dp[i - 1][j][1]
                
                if (dp[i][j][0] == False) and (c_rCount[i - 1][1] <= j):
                    dp[i][j][0] |= dp[i - 1][j - c_rCount[i - 1][1]][0]
                    if dp[i - 1][j - c_rCount[i - 1][1]][0] == True:
                        #in this combination, client i is selected
                        dp[i][j][1].append(c_rCount[i - 1])
                        dp[i][j][1].extend(dp[i - 1][j - c_rCount[i - 1][1]][1])
        for j in reversed(range(int(summed / 2 + 1))):
            if dp[n][j][0]:
                results[0] = dp[n][j][1]
                #print len(dp[n][j][1])
                #print dp[n][j]
                break
        if len(results[0]) > 0:
            clients = [x[0] for x in results[0]]
            for rec in c_rCount:
                if rec[0] not in clients:
                    results[1].append(rec)
        else:
            print 'spliting failed, the length of first half split result is 0. exiting'
            exit(-1)
        print 'bi-partition result:'
        print '[1]: ' + str(sum([x[1] for x in results[0]]))
        print '[2]: ' + str(sum([x[1] for x in results[1]]))
        return results
    
    res = [[] for x in xrange(numclients)]
    res[0] = client_reqCount

    folds = int(math.log(numclients) / math.log(2))
    step = numclients * 2
    for i in range(0, folds):
        step = step / 2
        for j in range(0, 2**i):
            results = split_req(res[j * step])
            res[j * step] = results[0]
            res[j * step + int(step / 2)] = results[1]
            #res = results
    #with open('test.txt', 'w') as f:
    #    for item in res:
    #        f.write("%s\n" % item)
    #        f.write("\n")
    print 'final work split:'

    i = -1
    ret = [[] for j in range(0, numclients)]
    print len(res)
    print i
    #print ret[numclients - 1]
    for elem in res:
        print i
        print len(elem)
        #print elem
        i += 1
        print i
        for cli in elem:
            #print cli[0]
            #print clientToReqs[cli[0]]
            ret[i].extend(clientToReqs[cli[0]])
           
    return ret
def organize(requests, out_trace, numclients, getonly):
    organized = [[] for x in xrange(numclients)]
    clientTOThreads = {}
    clientToReqs = defaultdict(list)
    
    with open(out_trace, 'r') as f:
        blob = json.load(f)
    print "load number of unique get requests: " + str(len(blob)) 
    print "load number of replay requests: " + str(len(requests)) 
    
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
	    if True == getonly:
		continue
            request['size'] = r['size']
            request['method'] = 'PUT'
            
        clientToReqs[r['client']].append(request)
    
    i = 0
    """for cli in clientToReqs:
        #req = clireqlst[0]
        #try:
        #    threadid = clientTOThreads[cli]
        #    organized[threadid].extend(clientToReqs[cli])
        #except Exception as e:
        organized[i%numclients].extend(clientToReqs[cli])
        clientTOThreads[cli] = i%numclients
        i += 1    """
             
    print ("number of clients:", len(clientToReqs)) 
    client_reqCount = []
    print 'clientToReqs: ' + str(len(clientToReqs))
    for k, v in clientToReqs.iteritems():
        client_reqCount.append([k, len(v)])
    #print clientToReqs[client_reqCount[0][0]]
    #print client_reqCount[0]
    organized = bi_load_balance(numclients, client_reqCount, clientToReqs)
    print 'bi-partitioned...printing each thread...'
    for elem in organized:
        print 'length: ' + str(len(elem))
    
    before = 0
    
    for clireqlst in organized:
        clireqlst.sort(key= lambda x: x['delay'])
        i = 0
        for r in clireqlst:
	    #print r
            if 0 == i:
                r['sleep'] = 0
                before = r['delay']
                i += 1
            else:
                r['sleep'] = (r['delay'] - before).total_seconds()
                before = r['delay']
                i += 1
                
        print ("number of request for client:", i)
                
    #print organized
    totalcnt = sum([len(x) for x in organized])
    print ("total number of relay requests are: ", totalcnt)
    return organized
'''
def organize(requests, out_trace, numclients, getonly):
    organized = [[] for x in xrange(numclients)]
    clientTOThreads = {}
    clientToReqs = defaultdict(list)
    
    with open(out_trace, 'r') as f:
        blob = json.load(f)
    print "load number of unique get requests: " + str(len(blob)) 
    print "load number of replay requests: " + str(len(requests)) 
  
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
            if True == getonly:
                continue
            request['size'] = r['size']
            request['method'] = 'PUT'
            
        clientToReqs[r['client']].append(request)
    
    i = 0
    for cli in clientToReqs:
        #req = clireqlst[0]
        try:
            threadid = clientTOThreads[cli]
            organized[threadid].extend(clientToReqs[cli])
        except Exception as e:
            organized[i%numclients].extend(clientToReqs[cli])
            clientTOThreads[cli] = i%numclients
            i += 1    
             
    print ("number of client threads/ clients:", i)  
     
    before = 0
    
    for clireqlst in organized:
        clireqlst.sort(key= lambda x: x['delay'])
        i = 0
        for r in clireqlst:
        #print r
            if 0 == i:
                r['sleep'] = 0
                before = r['delay']
                i += 1
            else:
                r['sleep'] = (r['delay'] - before).total_seconds()
                before = r['delay']
                i += 1
                
        print ("number of request for client:", i)
                
    #print organized
    totalcnt = sum([len(x) for x in organized])
    print ("total number of relay requests are: ", totalcnt)
    return organized

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
        
    registries = []
    if 'registry' in inputs:
        registries.extend(inputs['registry'])
     
    print(registries)
 
<<<<<<< HEAD
    getonly = False
    if 'simulate' in inputs:
        if inputs['simulate']['getonly'] == True:
            getonly = True
            print("getonly or not?", getonly)
        
        tracetype = inputs['simulate']['tracetype']
        print ("tracetype is ", tracetype)
    else:
        getonly  = False
        tracetype = 'layer'

=======
    gettype = inputs['simulate']['gettype']       
    print("gettype layer or slice? ", gettype)
        
    wait = inputs['simulate']['wait']
    print ("wait or not? ", wait)
    
>>>>>>> fffe4e36a2abe5a1710a8aa889ae13386f1fbbc4
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
    
    if args.command == 'match':    
        if 'realblobs' in inputs['client_info']:
#             choseclis = extract_client_reqs(trace_files, threads, limit, tracetype)            
            realblob_locations = inputs['client_info']['realblobs'] # bin larg ob/specify set of layers(?) being tested
            tracedata, layeridmap = fix_put_id(trace_files, limit)
            match(realblob_locations, tracedata, layeridmap)
            return
	else:
	    print "please put realblobs in the config files"
	    return

<<<<<<< HEAD
    json_data = get_requests(trace_files, limit)#, getonly) # == init in cache.py
    config_client(registries, testmode) #requests, out_trace, numclients   
    print len(json_data) 
=======
    json_data = get_requests()#, getonly) # == init in cache.py
    config_client(registries, testmode, gettype, wait) #requests, out_trace, numclients   
         
>>>>>>> fffe4e36a2abe5a1710a8aa889ae13386f1fbbc4
    if args.command == 'warmup': 
        print 'warmup mode'
        warmup(json_data, interm, registries, threads)

    elif args.command == 'run':
        print 'run mode'
<<<<<<< HEAD
        data = organize(json_data, interm, threads, getonly)
        return
        #get_blobs(data, threads, out_file)#, testmode)
=======
        data = organize(json_data, interm, threads)
        get_blobs(data, threads, out_file)#, testmode)
>>>>>>> fffe4e36a2abe5a1710a8aa889ae13386f1fbbc4
    else:
        pass


if __name__ == "__main__":
    main()
