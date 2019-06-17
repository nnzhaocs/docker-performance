import os
import time
import random
from dxf import *
import threading
import json
from concurrent.futures import ProcessPoolExecutor
from rediscluster import StrictRedisCluster
import subprocess
from utilities import *
from uhashring import HashRing

###=========== this is a temperal directory =============>
layerdir = "/home/nannan/testing/layers"


def pull_from_registry(dgst, registry_tmp, newdir, type, uri):        
    result = {}
    size = 0
    global Testmode
        
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'
    dxf = DXF(registry_tmp, uri, insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
    fname = str(random.random())
    f = open(os.path.join(newdir, fname), 'w')
    now = time.time()
    try:
        for chunk in dxf.pull_blob(dgst, chunk_size=1024*1024):
            size += len(chunk)
	    if "traditionaldedup" == Testmode: 
            	f.write(chunk)
           # print("dxf object: ", dxf, "size: ", size, "hash: ", dgst)
    except Exception as e:
        if "expected digest sha256:" in str(e):
            onTime = 'yes: wrong digest'
        else:
            print("GET: dxf object: ", dxf, "hash: ", dgst, "dxf Exception:", e)
            onTime = 'failed: '+str(e)
            
    t = time.time() - now
    
    result = {'time': now, 'size': size, 'onTime': onTime, 'duration': t, "digest": fname, "type": type}
    print("Putting results for: ", fname, result)
    return result


def redis_stat_bfrecipe_serverips(dgst):
    global rj_dbNoBFRecipe
    key = "Blob:File:Recipe::"+dgst
    if not rj_dbNoBFRecipe.exists(key):
	"cannot find recipe for redis_stat_bfrecipe_serverips"
        return None
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    serverIps = []
    #print("bfrecipe: ", bfrecipe)
    for serverip in bfrecipe['ServerIps']:
        serverIps.append(serverip)
    return serverIps


def get_request_registries(r):
    global ring
    global Testmode
    uri = r['uri']
    layer_id = uri.split('/')[-1]
    #print layer_id
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


def get_layer_request(request):
    registries = []
    onTime_l = []
    results = {}
    global Testmode

    dgst = request['blob']      
    full_uri = request['uri']
    uri_trunks = full_uri.split('/')
    uri = uri_trunks[1] + uri_trunks[2]

    registries.extend(get_request_registries(request)) 
    threads = len(registries)
    print('registries list', registries)
    if not threads:
        print 'destination registries for this blob is zero! ERROR!' 
        return results           
    
    now = time.time()
    # get slice requests
    newdir = os.path.join(layerdir, str(threading.currentThread().ident), str(request['delay']), str(random.random()))
    mk_dir(newdir)
    compresstarsdir = os.path.join(newdir, "compresstarsdir")
    mk_dir(compresstarsdir)
    
    with ProcessPoolExecutor(max_workers = threads) as executor:
        futures = [executor.submit(pull_from_registry, dgst, registry, compresstarsdir, "slice", uri) for registry in registries]
        for future in futures:#.as_completed(timeout=60):
            #print("get_layer_request: future result: ", future.result(timeout=60))
            try:
                x = future.result()
                onTime_l.append(x)      
            except Exception as e:
                print('get_layer_request: something generated an exception: %s', e, dgst)
		print("registries: ", registries) 
    restoretime = time.time() - now 
    #print Testmode
    if 'sift' == Testmode:
        results = {'time': now, 'duration': restoretime, 'onTime': onTime_l, 'type': 'layer'}     
        return results
    
    decompressdir = os.path.join(newdir, "dgstdir", dgst)
    mk_dir(decompressdir)

    slicefilelst = []
    dgstlst = []
    now = time.time()
    if threads > 1:        
        for x in onTime_l:
            slicefilelst.append(os.path.join(compresstarsdir, x["digest"]))    
        with ProcessPoolExecutor(max_workers = len(slicefilelst)) as executor:
            futures = [executor.submit(decompress_tarball_gunzip, sf, decompressdir) for sf in slicefilelst]
            for future in futures:#.as_completed(timeout=60):
                #print("get_layer_request: future result: ", future.result(timeout=60))
                try:
                    x = future.result()
#                     onTime_l.append(x)      
                except Exception as e:
                    print('get_layer_request: something generated an exception: %s', e, dgst)
            print("dgst: ", slicefilelst) 
            
    decompress_time = time.time() - now 
    
    dgstcompressdir = os.path.join(newdir, "dgstcompressdir") #dgst+".tar.gz")
    mk_dir(dgstcompressdir)
    layerfile = os.path.join(dgstcompressdir, dgst+".tar.gz")

    now = time.time()       
    compress_tarball_gzip(layerfile, decompressdir)    
    compress_time = time.time() - now 
     
    now = time.time()
    #print "pushing to registries"
    full_uri = request['uri']
    uri_trunks = full_uri.split('/')
    uri = uri_trunks[1] + uri_trunks[2]
    push_random_registry(layerfile, uri) #dgstdir+tar.zip
    layer_transfer_time = time.time() - now 
    
    clear_extracting_dir(newdir) 
    
    results = {'time': now, 'duration': restoretime + decompress_time + compress_time + layer_transfer_time, 'onTime': onTime_l,
               'restoretime': restoretime, 'decompress_time': decompress_time, 'compress_time': compress_time, 'layer_transfer_time': layer_transfer_time,
               'type': 'layer'}
             
    return results

def push_random_registry(dgstfile, uri):
    registries = ['192.168.0.151:5000', '192.168.0.152:5000', '192.168.0.153:5000', '192.168.0.154:5000']
    registry_tmp = random.choice(registries)
    dxf = DXF(registry_tmp, uri, insecure=True) 

    try:
        dgst = dxf.push_blob(dgstfile)#fname
    except Exception as e:
        print("PUT: dxf object: ", dxf, "file: ", dgstfile, "dxf Exception: Got", e)
    

def get_manifest_or_normallayer_request(request):
    #print request
    dgst = request['blob']
    full_uri = request['uri']
    uri_trunks = full_uri.split('/')
    uri = uri_trunks[1] + uri_trunks[2]
    registries = []
  
    registries.extend(get_request_registries(request))
    if len(registries) == 0:
        print "get_manifest_request ERROR no registry########################"
#         return {}
    #print registries
    newdir = os.path.join(layerdir, str(threading.currentThread().ident), str(request['delay']), str(random.random()))
#     print newdir
    mk_dir(newdir)
    t = ''
    if 'manifest' in request['uri']:
        t = 'manifest'
    else:
        t = 'layer'       
    return pull_from_registry(dgst, registries[0], newdir, t, uri)
   

def pull_repo_request(r): 
    results = []
    
    if 'manifest' in r['uri']:
        print "get manifest request: "
        result = get_manifest_or_normallayer_request(r[0])
        results.append(result)
    else:
        global Testmode
    
#         if len(r) <= 1:
#             return results
        print Testmode
        if Testmode == 'nodedup':
            print "get normal layer requests: "
            result = get_manifest_or_normallayer_request(r)
    	#print "get normal: "+result
            results.extend(result)
        else:
            print "get layer requests: "
            result = get_layer_request(r)
            results.extend(result)
    return results
        
        
def push_layer_request(request):
    size = request['size']
    full_uri = request['uri']
    uri_trunks = full_uri.split('/')
    uri = uri_trunks[1] + uri_trunks[2]
    registries = []
    result = {}
    onTime = 'yes'
    if size > 0:
        registries.extend(get_request_registries(request)) 
        registry_tmp = registries[0]
        now = time.time()
        dxf = DXF(registry_tmp, uri, insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
        try:
            dgst = dxf.push_blob(request['data'])#fname
        except Exception as e:
            print("PUT: dxf object: ", dxf, "file: ", r['data'], "dxf Exception: Got", e.got, "Expected:", e.expected)
            if "expected digest sha256:" in str(e):
                onTime = 'yes: wrong digest'
            else:
                onTime = 'failed: ' + str(e)
        
        t = time.time() - now

        result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'push'}
        return result
        

def push_manifest_request(request):
    return push_layer_request(request)
            
            
def push_repo_request(r):
    results = []
    if 'manifest' in r['uri']:
        result = push_manifest_request(r)
        results.append(result)
    else:
        result = push_layer_request(r)
        results.append(result)
    return results
        
        
def send_requests(requests):
    results_all = [] 
    if not len(requests):
	return results_all

    for r in requests:
	#print r
        if 'GET' == r['method']:
            print "get repo request: "
# 	    print r
            results = pull_repo_request(r)
        elif 'PUT' == r['method']:
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
    

def config_client(num_client_threads, registries_input, test_mode): 
    global ring
    global rj_dbNoBFRecipe
    global rjpool_dbNoBFRecipe
    global numthreads
    global registries
    global Testmode
    registries = registries_input
    numthreads = num_client_threads
    ring = HashRing(nodes = registries)
    Testmode = test_mode
    print("The testmode is:", Testmode)

    print registries
    if "192.168.0.170:5000" in registries:
        startup_nodes = startup_nodes_hulks
        print("==========> Testing HULKS <============: ", startup_nodes)
    else:    
        startup_nodes = startup_nodes_thors
        print("==========> Testing THORS <============: ", startup_nodes)
        
    rj_dbNoBFRecipe = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
    


    



