import os
import time
import random
from dxf import *
import threading
import json
from concurrent.futures import ProcessPoolExecutor
import subprocess
from utilities import *
from uhashring import HashRing

###=========== this is a temperal directory =============>
layerdir = "/home/nannan/testing/layers"


def pull_from_registry(dgst, registry_tmp, type, reponame, client):        
    result = {}
    size = 0
    global Testmode
        
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'    
    newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame    
    dxf = DXF(registry_tmp, newreponame.lower(), insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
    #print("newreponame: ", newreponame)   
    print("pull layer from registry, dgst: ", dgst)
    now = time.time()
    try:
        for chunk in dxf.pull_blob(dgst, chunk_size=1024*1024):
            size += len(chunk)
    except Exception as e:
        if "expected digest sha256:" in str(e):
            onTime = 'yes: wrong digest'
        else:
            print("GET: dxf object: ", dxf, "hash: ", dgst, "dxf Exception:", e)
            onTime = 'failed: '+str(e)
            
    t = time.time() - now
    
    result = {'time': now, 'size': size, 'onTime': onTime, 'duration': t, "digest": dgst, "type": type}
    
    print("pull: ", result)
    return result


def get_request_registries(r):
    global ring
    global Testmode
        
    uri = r['uri']
    layer_id = uri.split('/')[-1]
    
    if (r['method'] == 'PUT') or ('manifest' in r['uri']) or (Testmode == 'nodedup'):
        registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
        #print "layer: "+layer_id+"goest to registry: "+registry_tmp
        return [registry_tmp]
    else:
        dgst = r['blob'] 
        serverIps = redis_stat_recipe_serverips(dgst)
        #print"GET: ips retrieved from redis for blob "+dgst+" is "+str(serverIps)
        if not serverIps:
            registry_tmp = ring.get_node(layer_id)
            return [registry_tmp]
        return list(set(serverIps))

#key = 'Slice:Recipe::'+dgst
def redis_stat_recipe_serverips(dgst):
    global rediscli_dbrecipe
    global Gettype

    key = "Layer:Recipe::"+dgst    
    if not rediscli_dbrecipe.exists(key):
        print "################ cannot find recipe for redis_stat_recipe_serverips ############"
        return None
    recipe = json.loads(rediscli_dbrecipe.execute_command('GET', key))
    serverIps = []
    if "layer" == Gettype:
        return serverIps.append(recipe['MasterIp'])
    #print("recipe: ", recipe)
    elif 'slice' == Gettype:  
        for serverip in recipe['HostServerIps']:
            serverIps.append(serverip)
        return serverIps
    else:
        return serverIps


def get_slice_request(request):
    registries = []
    onTime_l = []
    results = {}
    global Testmode
    global Gettype

    dgst = request['blob']      
    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = request['client']

    registries.extend(get_request_registries(request)) 
    threads = len(registries)
    print('registries list', registries)
    
    if not threads:
        print 'destination registries for this blob is zero! ERROR!' 
        return results           
    
    # get slice requests    
    now = time.time()
    with ProcessPoolExecutor(max_workers = threads) as executor:
        futures = [executor.submit(pull_from_registry, dgst, registry, "SLICE", reponame, client) for registry in registries]
        for future in futures:#.as_completed(timeout=60):
            #print("get_slice_request: future result: ", future.result(timeout=60))
            try:
                x = future.result()
                onTime_l.append(x)      
            except Exception as e:
                print('get_slice_request: something generated an exception: %s', e, dgst)

    duration = time.time() - now 

    results = {'time': now, 'duration': duration, 'onTime': onTime_l, 'type': 'SLICE'}     
    return results
    

def get_manifest_or_normallayer_request(request):
    #print request
    dgst = request['blob']
    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = request['client']
    registries = []
  
    registries.extend(get_request_registries(request))
    if len(registries) == 0:
        print "get_manifest_request ERROR no registry########################"
        return {}
    
    t = ''
    if 'manifest' in request['uri']:
        t = 'MANIFEST'
    else:
        t = 'LAYER'  
             
    return pull_from_registry(dgst, registries[0], t, reponame, client)
   

def pull_repo_request(r): 
    results = []
    
    if 'manifest' in r['uri']:
        print "get manifest request: "
        result = get_manifest_or_normallayer_request(r)
        results.append(result)
    else:
        global Testmode
        global Gettype
        if Testmode == 'nodedup' or Gettype == 'layer':
            print "get normal layer requests: "
            result = get_manifest_or_normallayer_request(r)
            results.append(result)
        else:
            print "get layer requests: "
            result = get_slice_request(r)
            results.append(result)
    return results
        
        
def push_layer_request(request):
    size = request['size']
    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = request['client']
    
    registries = []
    result = {}
    onTime = 'yes'

    if 'manifest' in uri:
        type = 'MANIFEST'
    else:
        type = 'LAYER'

    newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
    #print("newreponame: ", newreponame)
    blobfname = ''
    # manifest: randomly generate some files
    if not request['data']:
        with open(str(os.getpid()), 'wb') as f:
            f.seek(size - 9)
            f.write(str(random.getrandbits(64)))
            f.write('\0')
        blobfname = str(os.getpid())
    else:
        blobfname = request['data']
    
    if size > 0:
        registries.extend(get_request_registries(request)) 
        registry_tmp = registries[0]
        dxf = DXF(registry_tmp, newreponame.lower(), insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
        
        now = time.time()
        try:
            dgst = dxf.push_blob(blobfname)#fname
        except Exception as e:
            print("PUT: dxf object: ", dxf, "file: ", request['data'], e)
            if "expected digest sha256:" in str(e):
                onTime = 'yes: wrong digest'
            else:
                onTime = 'failed: ' + str(e)
                
        t = time.time() - now
        clear_extracting_dir(str(os.getpid()))
	if 'LAYER' == type:
            result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHLAYER'}
	else:
	    result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHMANIFEST'}
	print("push: ", blobfname, result)
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
        print "################# empty request list ##############"
        return results_all

    print_cnt = 10
    totalcnt = len(requests)
    i = 0
    prev = 0
    accelerater = 8
    global Wait

    for r in requests:
        i += 1
        if print_cnt == i:
            print ("==============> processed ", i*1.0/totalcnt, " requests! <=============", totalcnt) 
        if True == Wait and r['sleep'] > prev:
            print "sleeping .... .... " + str(r['sleep'] - prev) + '/' + str(accelerater)
            time.sleep((r['sleep'] - prev)/accelerater)
            
        if 'GET' == r['method']:
            print "get repo request: "
            result = pull_repo_request(r)
        elif 'PUT' == r['method']:
            print "push repo request: "
            result = push_repo_request(r)
	else:
	    print "############# norecognized method #########"
	    print r['method']

        results_all.extend(result) 
        prev = result[0]['duration']

    return  results_all     
    

def config_client(registries_input, testmode, gettype, wait): 
    global ring
    global rediscli_dbrecipe
    global rjpool_dbNoBFRecipe

    global registries
    global Testmode
    global Gettype
    global Wait
    
    registries = registries_input
    ring = HashRing(nodes = registries)
    Testmode = testmode
    Gettype = gettype
    Wait = wait
    
    print("The testmode is: ", Testmode)
    print("The Gettype is: ", Gettype)
    print("The Wait is: ", Wait)

    print registries
    if "192.168.0.170:5000" in registries:
        startup_nodes = startup_nodes_hulks
        print("==========> Testing HULKS <============: ", startup_nodes)
    else:    
        startup_nodes = startup_nodes_thors
        print("==========> Testing THORS <============: ", startup_nodes)
        
    rediscli_dbrecipe = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
    


    



