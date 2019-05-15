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
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed


# app = Bottle()

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

def pull_from_registry(dgst, registry_tmp):        
    result = {}
    size = 0
    now = time.time()
         
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'
    dxf = DXF(registry_tmp, 'test_repo', insecure=True)
    try:
        for chunk in dxf.pull_blob(dgst, chunk_size=1024*1024):
            size += len(chunk)
           # print("dxf object: ", dxf, "size: ", size, "hash: ", dgst)
    except Exception as e:
        #print("GET: dxf object: ", dxf, "hash: ", dgst, "dxf Exception:", e)
        if "expected digest sha256:" in str(e):
            onTime = 'yes: wrong digest'
        else:
            onTime = 'failed: '+str(e)
            
    t = time.time() - now
    
    result = {'time': now, 'size': size, 'onTime': onTime, 'duration': t}
    #print("Putting results for: ", dgst, result)
    return result


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

    uri = r['uri']
    layer_id = uri.split('/')[-1]

    if r['method'] == 'PUT' or 'manifest' in r['uri']:
        registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
        #print "layer: "+layer_id+"goest to registry: "+registry_tmp
        return [registry_tmp]
    else:

        dgst = r['blob'] 
        serverIps = redis_stat_bfrecipe_serverips(dgst)
        #print"GET: ips retrieved from redis for blob "+dgst+" is "+str(serverIps)
        if not serverIps:
            registry_tmp = ring.get_node(layer_id)
            return [registry_tmp]
        return list(set(serverIps))


def get_layer_request(request):
    registries = []
    onTime_l = []
    results = {}
    
    dgst = request['blob']      
    registries.extend(get_request_registries(request)) 
    threads = len(registries)
    print('registries list', registries)
    if not threads:
        print 'destination registries for this blob is zero! ERROR!'            
    
    now = time.time()
            
    with ProcessPoolExecutor(max_workers = threads) as executor:
        futures = [executor.submit(pull_from_registry, dgst, registry) for registry in registries]
        for future in futures:#.as_completed(timeout=60):
            #print("get_layer_request: future result: ", future.result(timeout=60))
            try:
                x = future.result(timeout=60)
                onTime_l.append(x)      
            except Exception as e:
                print('get_layer_request: something generated an exception: %s', e, dgst)
		print("registries: ", registries) 
    t = time.time() - now   
    results = {'time': now, 'duration': t, 'onTime': onTime_l}
    #print("onTime_l:", onTime_l)        
    #print("results: ", results)            
    return results


def get_manifest_request(request):
    dgst = request['blob']
    registries = []
    registries.extend(get_request_registries(request))
    
    return pull_from_registry(dgst, registries[0])
    
    
def get_layers_requests(r):
    results = []
    with ProcessPoolExecutor(max_workers = numthreads) as executor:
        futures = [executor.submit(get_layer_request, glreq) for glreq in r]
        for future in futures:#.as_completed(timout=60):
            #print("get_layers_requests: future result: ", future.result())
            try:
                x = future.result(timeout=60)
                results.append(x)
                #return results
            except Exception as e:
                print('get_layers_requests: something generated an exception: %s', e)    
    
    return results


def pull_repo_request(r): 
    results = []
    result = get_manifest_request(r[0])
    results.append(result)
    
    if len(r) > 1:
        result = get_layers_requests(r[1:])
        results.extend(result)
    return results
        
        
def push_layer_request(request):
    size = request['size']
    registries = []
    result = {}
    onTime = 'yes'
    if size > 0:
        registries.extend(get_request_registries(request)) 
        registry_tmp = registries[0]
        now = time.time()
        dxf = DXF(registry_tmp, 'test_repo', insecure=True)
        try:
            dgst = dxf.push_blob(request['data'])#fname
        except Exception as e:
            print("PUT: dxf object: ", dxf, "file: ", r['data'], "dxf Exception: Got", e.got, "Expected:", e.expected)
            if "expected digest sha256:" in str(e):
                onTime = 'yes: wrong digest'
            else:
                onTime = 'failed: ' + str(e)
        
        t = time.time() - now

        result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size}
        return result
        

def push_manifest_request(request):
    return push_layer_request(request)

        
def push_layers_requests(r):
    results = []
    with ProcessPoolExecutor(max_workers = numthreads) as executor:
        futures = [executor.submit(push_layer_request, plreq) for plreq in r]
        for future in futures:#.as_completed(timeout=60):
            #print(future.result())
            try:
                x = future.result(timeout=60)
                results.append(x)    
            except Exception as e:
                print('push_layers_requests: something generated an exception: %s', e)
    return results     
            
            
def push_repo_request(r):
    results = []
    if len(r) > 1:
        result = push_layers_requests(r[:len(r)-1])
        results.extend(result)
        result = push_manifest_request(r[0])
        results.append(result)
    else:
        result = push_manifest_request(r[0])
        results.append(result)
    return results
        
        
def send_requests(requests):
    results_all = [] 
    if not len(requests):
	return results_all

    for r in requests:
	#print r
        if 'manifest' in r[0]['uri'] and 'GET' == r[0]['method']:
            print "get repo request: "
	    print r
            results = pull_repo_request(r)
        elif 'manifest' in r[-1]['uri'] and 'PUT' == r[-1]['method']:
            print "push repo request: "
	    print r
            results = push_repo_request(r)
        else:
            print "weird request: "
            print r
            continue
    
        results_all.extend(results) 
	#print results_all
    return  results_all     


def config_client(redis_host, redis_port, num_client_threads, registries_input): 
    global ring
    global rj_dbNoBFRecipe
    global rjpool_dbNoBFRecipe
    global numthreads
    global registries
    registries = registries_input
    numthreads = num_client_threads
    ring = hash_ring.HashRing(registries)
    
    rjpool_dbNoBFRecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoBFRecipe)
    rj_dbNoBFRecipe = redis.Redis(connection_pool=rjpool_dbNoBFRecipe) 
    
                 
    


    



