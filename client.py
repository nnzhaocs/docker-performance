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
import threading
import rejson, redis, json
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from uhashring import HashRing
from rediscluster import StrictRedisCluster
#from scipy.stats.tests.test_stats import TestMode
import subprocess
from pipes import quote
# app = Bottle()
####
# NANNAN: tar the blobs and send back to master.
# maybe ignore.
####
            
##
# NANNAN: fetch the serverips from redis by using layer digest
##
###=========== this is ramdisk =============>
layerdir = "/home/nannan/testing/layers"
Testmode = ""

def pull_from_registry(dgst, registry_tmp, newdir):        
    result = {}
    size = 0
    now = time.time()
         
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'
    dxf = DXF(registry_tmp, 'test_repo', insecure=True)
    f = open(os.path.join(newdir, dgst), 'w')
    try:
        for chunk in dxf.pull_blob(dgst, chunk_size=1024*1024):
            size += len(chunk)
            f.write(chunk)
           # print("dxf object: ", dxf, "size: ", size, "hash: ", dgst)
    except Exception as e:
        if "expected digest sha256:" in str(e):
            onTime = 'yes: wrong digest'
        else:
            print("GET: dxf object: ", dxf, "hash: ", dgst, "dxf Exception:", e)
            onTime = 'failed: '+str(e)
            
    t = time.time() - now
    
    result = {'time': now, 'size': size, 'onTime': onTime, 'duration': t, "digest": dgst}
    print("Putting results for: ", dgst, result)
    return result


def redis_stat_bfrecipe_serverips(dgst):
    global rj_dbNoBFRecipe
    key = "Blob:File:Recipe::"+dgst
    if not rj_dbNoBFRecipe.exists(key):
	"cannot find recipe for redis_stat_bfrecipe_serverips"
        return None
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    serverIps = []
    print("bfrecipe: ", bfrecipe)
    for serverip in bfrecipe['ServerIps']:
        serverIps.append(serverip)
    return serverIps


def redis_set_bfrecipe_performance(dgst, decompress_time, compress_time, layer_transfer_time):
    global rj_dbNoBFRecipe
    key = "Blob:File:Recipe::"+dgst
    if not rj_dbNoBFRecipe.exists(key):
	print "cannot find recipe for redis_set_bfrecipe_performance"
        return None
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    bfrecipe['DurationCMP'] = compress_time
    bfrecipe['DurationDCMP'] = decompress_time  
    bfrecipe['DurationNTT'] = layer_transfer_time    
#     serverIps = []
    print("bfrecipe: ", bfrecipe)
#     for serverip in bfrecipe['ServerIps']:
#         serverIps.append(serverip)
    value = json.dumps(bfrecipe)
#     print value
    rj_dbNoBFRecipe.set(key, value)
    return True


def get_request_registries(r):
    global ring

    uri = r['uri']
    layer_id = uri.split('/')[-1]

    if r['method'] == 'PUT' or 'manifest' in r['uri'] or Testmode == 'nodedup':
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


def compress_tarball_gzip(dgstfile, dgstdir): #.gz
#     start = time.time()

    cmd = 'tar -zcvf %s %s' % (dgstfile, dgstdir)
    print('The shell command: %s', cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: exit code: %s; %s###################',
                      dgstdir, e.returncode, e.output)
        return False

#     elapsed = time.time() - start
    print('process layer_id:%s : gzip compress tar archival, consumed time ==> %f s', dgstdir) #.gz
    return True

def decompress_tarball_gunzip(sf, dgstdir):
    # start = time.time()
    
    
    cmd = 'tar -zxf %s -C %s' % (sf, dgstdir)
    print('The shell command: %s', cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        if "Unexpected EOF in archive" in e.output:
            print('###################%s: Pass exit code: %s; %s###################',
                      dgstdir, e.returncode, e.output)
        print('###################%s: exit code: %s; %s###################',
                      sf, e.returncode, e.output)
        return False

    #elapsed = time.time() - start
    # logging.info('process layer_id:%s : gunzip decompress tarball, consumed time ==> %f s', cp_layer_tarball_name, elapsed)
    print('FINISHED! to ==========> %s', dgstdir)
    return True


def clear_extracting_dir(dir):
    """clear the content"""
#     if not os.path.isdir(dir):
#         logging.error('###################%s is not valid###################', layer_dir)
#         return False

    cmd4 = 'rm -rf %s' % (dir+'*')
    print('The shell command: %s', cmd4)
    try:
        subprocess.check_output(cmd4, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: exit code: %s; %s###################',
                      dir, e.returncode, e.output)
        return False

    return True


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
        return results           
    
    now = time.time()
    #threads = 1        ##################
    newdir = os.path.join(layerdir, str(threading.currentThread().ident), str(request['delay']))
    mk_dir(newdir)
    with ProcessPoolExecutor(max_workers = threads) as executor:
        futures = [executor.submit(pull_from_registry, dgst, registry, newdir) for registry in registries]
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
    
    dgstdir = os.path.join(newdir, dgst)
     
    now = time.time()
    if len(threads) > 1:
        dgstlst = []
        for x in onTime_l:
            slicefilelst.append(os.path.join(newdir, x["digest"]))    
        with ProcessPoolExecutor(max_workers = len(dgstlst)) as executor:
            futures = [executor.submit(decompress_tarball_gunzip, sf, dgstdir) for sf in slicefilelst]
            for future in futures:#.as_completed(timeout=60):
                #print("get_layer_request: future result: ", future.result(timeout=60))
                try:
                    x = future.result(timeout=60)
#                     onTime_l.append(x)      
                except Exception as e:
                    print('get_layer_request: something generated an exception: %s', e, dgst)
            print("dgst: ", dgstlst) 
            
    decompress_time = time.time() - now 
    
    dgstfile = os.path.join(newdir, dgst+".tar.gz")  
    now = time.time()       
    compress_tarball_gzip(dgstfile, dgstdir)    
    compress_time = time.time() - now 
     
    now = time.time()
    push_random_registry(dgstfile) #dgstdir+tar.zip
    layer_transfer_time = time.time() - now 
    
    redis_set_bfrecipe_performance(dgst, decompress_time, compress_time, layer_transfer_time) 
    clear_extracting_dir(newdir)          
    return results

def push_random_registry(dgst):
    registries = ['192.168.0.151:5000', '192.168.0.152:5000', '192.168.0.153:5000', '192.168.0.154:5000', '192.168.0.156:5000']
    registry_tmp = random.choice(registries)
    dxf = DXF(registry_tmp, 'test_repo', insecure=True)
    try:
        dgst = dxf.push_blob(dgstfile)#fname
    except Exception as e:
        print("PUT: dxf object: ", dxf, "file: ", r['data'], "dxf Exception: Got", e.got, "Expected:", e.expected)
    

def mk_dir(newdir):
    #command = 'ls -l {}'.format(quote(filename))
    cmd1 = 'mkdir -pv {}'.format(quote(newdir))
#     print('The shell command: %s', cmd1)
    try:
        subprocess.check_output(cmd1, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: %s###################',
                      newdir, e.output)
        return False
    return True

def get_manifest_request(request):
    dgst = request['blob']
    registries = []
    registries.extend(get_request_registries(request))
    if len(registries) == 0:
        print "get_manifest_request ERROR no registry########################"
#         return {}
    newdir = os.path.join(layerdir, str(threading.currentThread().ident), str(request['delay']))
#     print newdir
    mk_dir(newdir)
    return pull_from_registry(dgst, registries[0], newdir)
    
    
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


def get_normal_layers_requests(r):
    results = []
    with ProcessPoolExecutor(max_workers = numthreads) as executor:
        futures = [executor.submit(get_manifest_request(req)) for req in r]
        for future in futures:#.as_completed(timout=60):
#             print("get_normal_layers_requests: future result: ", future.result())
            try:
                x = future.result(timeout=60)
                results.append(x)
                #return results
            except Exception as e:
                print('get_normal_requests: something generated an exception: %s', e)    
    
    return results
    

def pull_repo_request(r): 
    results = []
    print "get manifest request: "
    result = get_manifest_request(r[0])
    results.append(result)
    
    if len(r) <= 1:
        return results
    print Testmode
    if Testmode == 'nodedup':
	print "get normal layer requests: "
        result = get_normal_layers_requests(r[1:])
        results.extend(result)
    else:
	print "get layer requests: "
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
# 	    print r
            results = pull_repo_request(r)
        elif 'manifest' in r[-1]['uri'] and 'PUT' == r[-1]['method']:
            print "push repo request: "
# 	    print r
            results = push_repo_request(r)
        else:
            print "weird request: "
#             print r
            continue
    
        results_all.extend(results) 
	#print results_all
    return  results_all     


# def get_res_fromRedis():
#     global rj_dbNoBFRecipe
    

def config_client(num_client_threads, registries_input, test_mode): 
    global ring
    global rj_dbNoBFRecipe
    global rjpool_dbNoBFRecipe
    global numthreads
    global registries
    registries = registries_input
    numthreads = num_client_threads
    ring = HashRing(nodes = registries)
    Testmode = test_mode
    
#     rjpool_dbNoBFRecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoBFRecipe)
#     rj_dbNoBFRecipe = redis.Redis(connection_pool=rjpool_dbNoBFRecipe) 
    startup_nodes = [
            {"host": "192.168.0.170", "port": "7000"}, 
            {"host": "192.168.0.170", "port": "7001"},
            {"host": "192.168.0.171", "port": "7000"}, 
            {"host": "192.168.0.171", "port": "7001"},
            {"host": "192.168.0.172", "port": "7000"}, 
            {"host": "192.168.0.172", "port": "7001"},
            {"host": "192.168.0.174", "port": "7000"}, 
            {"host": "192.168.0.174", "port": "7001"},
            {"host": "192.168.0.176", "port": "7000"}, 
            {"host": "192.168.0.176", "port": "7001"},
            {"host": "192.168.0.177", "port": "7000"}, 
            {"host": "192.168.0.177", "port": "7001"},
            {"host": "192.168.0.178", "port": "7000"}, 
            {"host": "192.168.0.178", "port": "7001"},
            {"host": "192.168.0.179", "port": "7000"}, 
            {"host": "192.168.0.179", "port": "7001"},
            {"host": "192.168.0.180", "port": "7000"},
            {"host": "192.168.0.180", "port": "7001"}]
    rj_dbNoBFRecipe = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
    
    """
    {u'SliceSize': 166, u'DurationCP': 0.000751436, u'DurationCMP': 3.7068e-05, u'ServerIp': u'192.168.0.171', u'DurationML': 0.000553802, u'DurationNTT': 3.7041e-05, u'DurationRS': 0.001379347}
    startup_nodes = [
             {"host": "192.168.0.170", "port": "7000"}, \
            {"host": "192.168.0.170", "port": "7001"}, \
            {"host": "192.168.0.171", "port": "7000"},  \
            {"host": "192.168.0.171", "port": "7001"}, \
             {"host": "192.168.0.172", "port": "7000"},  \
            {"host": "192.168.0.172", "port": "7001"}, \
            {"host": "192.168.0.174", "port": "7000"}, \
             {"host": "192.168.0.174", "port": "7001"},\
             {"host": "192.168.0.176", "port": "7000"}, \
             {"host": "192.168.0.176", "port": "7001"},\
             {"host": "192.168.0.177", "port": "7000"}, \
             {"host": "192.168.0.177", "port": "7001"},\
             {"host": "192.168.0.178", "port": "7000"}, \
            {"host": "192.168.0.178", "port": "7001"},\
             {"host": "192.168.0.179", "port": "7000"}, \
             {"host": "192.168.0.179", "port": "7001"},\
            {"host": "192.168.0.180", "port": "7000"},\
             {"host": "192.168.0.180", "port": "7001"}]
      
    """             
    


    



