from bottle import route, run, request, static_file, Bottle, response
import hash_ring
import sys, getopt
import yaml
import os
import requests
import json
from argparse import ArgumentParser
from optparse import OptionParser
import time
import socket
import random
import pdb
from multiprocessing import Process, Queue
from dxf import *

import rejson, redis, json

app = Bottle()

dbNoBlob = 0 
dbNoFile = 1
dbNoBFRecipe = 2

####
# NANNAN: tar the blobs and send back to master.
# maybe ignore.
####
            
##
# NANNAN: fetch the serverips from redis by using layer digest
##
def pull_from_registry(wait, dgst, registry_tmp, startTime, onTime_q):
#     while True:
#         registry_tmp = registry_q.get()        
    results = []
    size = 0
    t = 0
    t = time.time()
         
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'
    dxf = DXF(registry_tmp, 'test_repo', insecure=True)
    try:
        for chunk in dxf.pull_blob(dgst, chunk_size=1024*1024):
            size += len(chunk)
            print("dxf object: ", dxf, "size: ", size, "hash: ", dgst)
    except Exception as e:
        print("GET: dxf object: ", dxf, "hash: ", dgst, "dxf Exception:", e)
        if "expected digest sha256:" in str(e):
            onTime = 'yes: wrong digest'
        else:
            onTime = 'failed: '+str(e)
            
    t = time.time() - t
    
    results.append({'size': size, 'onTime': onTime, 'duration': t})
    print("Putting results for: ", dgst)
    
    onTime_q.put(results)


def redis_stat_bfrecipe_serverips(dgst):
    global rj_dbNoBFRecipe
    key = "Blob:File:Recipe::"+dgst
    if not rj_dbNoBFRecipe.exists(key):
        return None
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('JSON.GET', key))
    serverIps = []
#    print("bfrecipe: ", bfrecipe)
    for serverip in bfrecipe['ServerIps']:
        serverIps.append(serverip)
    return serverIps


def get_request_registries(r):
    global ring

    dgst = r['blob'] 
    uri = r['uri']
    layer_id = uri.split('/')[-1]

    if r['method'] == 'PUT':
        registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
        print "layer: "+req['blob']+"goest to registry: "+registry_tmp
        return [registry_tmp]
    else:
        serverIps = redis_stat_bfrecipe_serverips(dgst)
        print"GET: ips retrieved from redis for blob "+dgst+" is "+str(serverIps)
        if not serverIps:
            registry_tmp = ring.get_node(layer_id)
            return [registry_tmp]
        return list(set(serverIps))


def send_requests(wait, requests, startTime, q):
    results = []
    for r in requests:
        print("request in send_requests: ", r)
        size = 0
        t = 0
        registries = []
        processes = []
        start = startTime + r['delay']
        print("request:", r)
        onTime = 'no'

        if r['method'] == 'GET':

            dgst = r['blob']
            
            registries.extend(get_request_registries(r)) 
            threads = len(registries)
            print('registries list', registries)
            if not threads:
                print 'destination registries for this blob is zero! ERROR!'            

            onTime_q = Queue()
#             registry_q = Queue()
#             [registry_q.put(i) for i in registries]
            
            now = time.time()
            if start > now and wait is True:
                onTime = 'yes'
                time.sleep(start - now)
            t = time.time()

            for i in range(threads):
                p = Process(target=pull_from_registry, args=(wait, dgst, registries[i], startTime, onTime_q))
                p.start()
                processes.append(p)
                
            for p in processes:
                p.join()
                
            t = time.time() - t
	    onTime_l = []
            while not onTime_q.empty():
            	onTime_l.extend(onTime_q.get())
	    print("onTime_l: ", onTime_l)
#<<<<<<< HEAD
               
#            results.append({'time': now, 'duration': t, 'onTime': onTime_l})
#=======
                
            results.append({'time': now, 'duration': t, 'onTime_l': onTime_l, 'onTime': None, 'size': None})
#>>>>>>> f1a800648585e2e253c7da7ed0becb44aa29f22e
#             pull_rsp_q.put(results)   
        
            print 'processes joined, send requests continuing'
        else:                  
            size = r['size']
            if size > 0:
                now = time.time()
                if start > now and wait is True:
                    time.sleep(start - now)
                now = time.time()
                registries.extend(get_request_registries(r)) 
                registry_tmp = registries[0]
                dxf = DXF(registry_tmp, 'test_repo', insecure=True)
                try:
                    dgst = dxf.push_blob(r['data'])#fname
                except Exception as e:
                    print("PUT: dxf object: ", dxf, "file: ", r['data'], "dxf Exception: Got", e.got, "Expected:", e.expected)
                    if "expected digest sha256:" in str(e):
                        onTime = 'yes: wrong digest'
                    else:
                        onTime = 'failed: '+str(e)
 
                t = time.time() - now
 
#<<<<<<< HEAD
#                results.append({'time': now, 'duration': t, 'onTime': onTime, 'size': size})
#=======
                results.append({'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'onTime_l': None})
#>>>>>>> f1a800648585e2e253c7da7ed0becb44aa29f22e
	print 'time: '+str(now)+', duration: '+str(t)
	print('onTime: ', onTime)
        q.put(results)

################################
# NANNAN: forward to registries according to cht
################################
def get_messages(q):
    while True:
        msg = q.get()
        masterip = msg[0]
 
        requests = json.loads(msg[1])
#         put_rand = requests[0]['random']
        threads = requests[0]['threads']
        ID = requests[0]['id']
        master = (masterip, requests[0]['port'])
#         registry = requests[0]['registry']
        wait = requests[0]['wait']
        print master, ID, threads
        processes = []
        process_requests = []
        delayed = []
        for i in range(threads):
            process_requests.append([])
            delayed.append(0)
 
        for r in requests[1:]:
            i = 0
            for j in range(len(delayed)):
                if delayed[j] < delayed[i]:
                    i = j
            if delayed[i] < r['delay']:
                delayed[i] = r['delay'] + r['duration']
            else:
                delayed[i] += r['duration']
                 
            process_requests[i].append(r)
 
        requests = [{'id': ID}]
 
        startTime = time.time()
        rq = Queue()
        for i in range(threads):
#             first = registry.pop(0)
#             registry.append(first)
            p = Process(target=send_requests, args=(wait, process_requests[i], startTime, rq))
            p.start()
            processes.append(p)
 
        for i in range(threads):
            requests.extend(rq.get())
 
        for p in processes:
            p.join()
        print 'processes joined, sending response'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        err = False
        try:
            sock.connect(master)
            sock.sendall(json.dumps(requests))
        except Exception as inst:
            print("exception: ", inst)
            print "Error sending info, writing to file"
            err = True
        if err is True:
            with open('error_output', 'w') as f:
                f.write(json.dumps(requests))
        sock.close()
        print 'finished'
  

@app.route('/up', method="POST")
def sen():
    if 'application/json' in request.headers['Content-Type']:
        app.queue.put((request.environ.get('REMOTE_ADDR'), request.body.read()))
        return 'gotcha :D'

  
def main():
    ip = "0.0.0.0"
    registries = []
                
    parser = ArgumentParser(description='registry-helper, helping registry to do a global dedup or slimmer ops.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    parser.add_argument('-p', '--port', dest='ppppp', type=str, required=False, help = 'identifier')
    parser.add_argument('-c', '--command', dest='command', type=str, required=False, help= 'registry-testing command. Possible commands: TestGloablDedup, etc,.')

    args = parser.parse_args()
    
    config = file(args.input, 'r')
    
    try:
        inputs = yaml.load(config)
    except Exception as inst:
        print 'error reading config file'
        print inst
        exit(-1)

    verbose = False
    if 'verbose' in inputs:
        if inputs['verbose'] is True:
            verbose = True
            print 'Verbose Mode'

    if 'registry' in inputs:
        registries.extend(inputs['registry'])

    if 'client_port' not in inputs['client_info']:
        if verbose:
            print 'client port not specified, assuming 8082'
            port = 8082
    else:
        port = inputs['client_info']['client_port']
        if verbose:
            print 'client port: ' + str(port)     
            
            
    global app
    global ring
    global rj_dbNoBFRecipe
    global rjpool_dbNoBFRecipe
#### connect to redis!
    if 'redis' not in inputs:
        print 'please config redis for helper!'
    else:
        redis_host = inputs['redis']['host']
        redis_port = inputs['redis']['port']
        if verbose:
            print 'redis: host:'+str(redis_host)+',port:'+str(redis_port)
            
#     rj = rejson.Client(host=redis_host, port=redis_port)
    rjpool_dbNoBFRecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoBFRecipe)
    rj_dbNoBFRecipe = redis.Redis(connection_pool=rjpool_dbNoBFRecipe)  
    
    print(registries)
    ring = hash_ring.HashRing(registries)             
    
    if args.command == 'TestGlobalDedup':
        if verbose: 
            print 'test global dedup mode'

    
    app.queue = Queue()
    backend = Process(target=get_messages, args=[app.queue])
    backend.start()
    run(app, host=ip, port=port, quiet=True, numthreads=1)

if __name__ == "__main__":
    main()

