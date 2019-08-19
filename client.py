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


def pull_from_registry(dgst, registry_tmp, type, reponame, client):        
    result = {}
    size = 0
    global Testmode
        
    if ":5000" not in registry_tmp:
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'    
    #newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame    
    
    if Testmode != "nodedup":
        newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
    else:
        newreponame = "testrepo"

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


def push_to_registry(blobfname, registry, newreponame, tp):    
    
    dxf = DXF(registry, newreponame.lower(), insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
    
    try:
        dgst = dxf.push_blob(blobfname)
    except Exception as e:
            print("PUT/WARMUP: dxf object: ", dxf, "file: ", blobfname, e)
            dgst = 'bad'
            onTime = 'failed: '+str(e)  
            
    result = {'registry': registry, 'onTime': onTime, 'dgst': dgst}                           
    print result  
    return result


def get_write_registries(r):
    global ring
    global ringdedup
    
    global testmode
    global replica_level
     
    global siftmode
    global hotratio
    global nondedupreplicas
    
    global hotlayers
         
    uri = r['uri']
    id = uri.split('/')[-1]
    # *************** registry_tmps: [x, x, dedup] ************  
    registry_tmps = []
    if ('manifest' in r['uri']) or (Testmode == 'nodedup'): 
        noderange = ring.range(id, replica_level, True)
        for i in noderange:
            registry_tmps.append(i)
    elif testmode == 'sift': 
        if 'standard' == siftmode:
            # *********** nondedupreplicas send to primary nodes ************  
            noderange = ring.range(id, nondedupreplicas, True)
            for i in noderange:
                registry_tmps.append(i)
            # *********** 1 replica send to dedup nodes ************      
            registry_tmps.append(ringdedup.get_node(id))
        elif 'selective' == siftmode:
            if id in hotlayers:
                noderange = ring.range(id, replica_level, True)
                for i in noderange:
                    registry_tmps.append(i)
            else:
                registry_tmps.append(ring.get_node(id))
                registry_tmps.append(ringdedup.get_node(id))
                 
    elif testmode == 'restore':
        registry_tmps.append(ringdedup.get_node(id)) 
            
    return registry_tmps 


def get_read_registries(r):
    global ring
    global ringdedup
    
    global testmode
    global replica_level
      
    global siftmode
    global hotratio
    global nondedupreplicas
     
    global hotlayers
       
    uri = r['uri']
    layer_id = uri.split('/')[-1] #(r['method'] == 'PUT') or 
    
    registry_tmps = []
    if ('manifest' in r['uri']) or (Testmode == 'nodedup'):
        registry_tmps = get_write_registries(r)
        registry_tmp = random.choice(registry_tmps) 
        #ring.get_node(layer_id) # which registry should store this layer/manifest?
        #print "layer: "+layer_id+"goest to registry: "+registry_tmp
        return [registry_tmp]
    elif testmode == 'restore':
        dgst = r['blob'] 
        serverIps = redis_stat_recipe_serverips(dgst)
        #print"GET: ips retrieved from redis for blob "+dgst+" is "+str(serverIps)
        if not serverIps:
            registry_tmp = ringdedup.get_node(layer_id)
            return [registry_tmp]
    elif testmode == 'sift':
        registry_tmps = get_write_registries(r)
        registry_tmp = random.choice(registry_tmps[:len(registry_tmps)-1])
        
    return registry_tmp 


def redis_stat_recipe_serverips(dgst):
    global rediscli_dbrecipe
    #global Gettype

    key = "Layer:Recipe::"+dgst    
    if not rediscli_dbrecipe.exists(key):
        print "################ cannot find recipe for redis_stat_recipe_serverips ############" + dgst
        return None
    recipe = json.loads(rediscli_dbrecipe.execute_command('GET', key))
    serverIps = []
    #if "layer" == Gettype:
    return serverIps.append(recipe['MasterIp'])
    #else:
    #    return serverIps


def get_request_registries(r):
    registry_tmps = []
    if 'GET' == r['method']:
        registry_tmps = get_read_registries(r)
    elif 'PUT' == r['method']:
        registry_tmps = get_write_registries(r)
        
    return registry_tmps
          

def get_request(request):
    #print request
    results = []
    
    dgst = request['blob']
    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = request['client']
    registries = []
  
    registries.extend(get_request_registries(request))
    if len(registries) == 0:
        print "get_manifest_request ERROR no registry ######################## "+dgst
        return {}
    
    t = ''
    if 'manifest' in request['uri']:
        t = 'MANIFEST'
        print "get manifest request: "
    else:
        t = 'LAYER'  
        print "get layer requests: "
             
    result = pull_from_registry(dgst, registries[0], t, reponame, client)
    results.append(result)
    

def put_request(request):
    results = []
    
    registries.extend(get_request_registries(request))
    result = distribute_put_requests(request, 'PUT', registries)
    results.append(result)
    return results    
        
def distribute_put_requests(request, tp, registries):
    
    all = {}
    trace = {}
    
    size = request['size']
    uri = request['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = request['client']
    id = uri.split('/')[-1]
    
    newreponame = ''
    dgst = ''
    
    registries = []
    result = {}
    onTime = 'yes'
    
    global Testmode

    if 'manifest' in uri:
        type = 'MANIFEST'
        print "put manifest request: "
    elif tp == 'PUT':
        type = 'LAYER'
        print "put layer request: "
    elif tp == 'WARMUP':
        type = 'WARMUPLAYER'
        print "warmup layer request: "
    
    if Testmode != "nodedup":
        newreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
    else:
        newreponame = "testrepo"
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
     
    now = time.time()        
    with ProcessPoolExecutor(max_workers = len(registries)) as executor:
        futures = [executor.submit(push_to_registry, blobfname, registry, newreponame) for registry in registries]
        for future in futures:#.as_completed(timeout=60):
            #print("get_slice_request: future result: ", future.result(timeout=60))
            try:
                x = future.result()
                if 'failed' in x['onTime']:
                    onTime = x['onTime']
                else:
                    dgst = x['dgst']
#                 onTime_l.append(x)      
            except Exception as e:
                print('send_warmup_thread: something generated an exception: %s', e, uri)   

    t = time.time() - now
       
    clear_extracting_dir(str(os.getpid()))
    
    if 'manifest' in uri and tp == 'WARMUP':
        tpp = 'warmupmanifest'          
    elif 'WARMUPLAYER' == type:
        tpp = 'warmuplayer'

    if 'WARMUP' == tp:    
        result = {'time': now, 'size': request['size'], 'onTime': onTime, 'duration': t, 'type': tpp}
        print result
        trace[type+id] = dgst
        all = {'trace': trace, 'result': result}
        return all    
    elif 'PUT' == tp:
        if 'manifest' not in uri:
            result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHLAYER'}
    	else:
    	    result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHMANIFEST'}
    	print("push: ", blobfname, result)
        return result
        
               
def send_requests(requests):
    results_all = [] 
    if not len(requests):
        print "################# empty request list ##############"
        return results_all

    print_cnt = 10
    totalcnt = len(requests)
    i = 0
    prev = 0
    global Accelerater #= 8
    global Wait

    for r in requests:
        i += 1
        if print_cnt == i:
            print ("==============> processed ", i*1.0/totalcnt, " requests! <=============", totalcnt) 
        if True == Wait and r['sleep'] > prev:
            print "sleeping .... .... " + str(r['sleep'] - prev) + '/' + str(Accelerater)
            time.sleep((r['sleep'] - prev)/Accelerater)
            
        if 'GET' == r['method']:
            print "get repo request: "
            result = get_request(r)
        elif 'PUT' == r['method']:
            print "push repo request: "
            result = put_request(r)
	else:
	    print "############# norecognized method #########"
	    print r['method']

        results_all.extend(result) 
        prev = result[0]['duration']

    return  results_all     
    

def config_client(ring_input, ringdedup_input, dedupregistries, hotlayers_input, testmode, wait, accelerater): 

    global rediscli_dbrecipe
    global rjpool_dbNoBFRecipe
   
    global Testmode
    #global Gettype
    global Wait
    global Accelerater
    
    global ring  
    global ringdedup
    global hotlayer
      
    ring = ring_input
    ringdedup = ringdedup_input
    hotlayer = hotlayers_input
        
    Testmode = testmode
    #Gettype = gettype
    Wait = wait
    Accelerater = accelerater
    
    print("The testmode is: ", Testmode)
    #print("The Gettype is: ", Gettype)
    print("The Wait is: ", Wait)
    print("The Accelerater is: ", Accelerater)

    print("===========> Testing dedupregistries <============", dedupregistries)
    
    if Testmode != 'nodedup':    
        if "192.168.0.17" in dedupregistries[0]:
            startup_nodes = startup_nodes_hulks
            print("==========> Testing dedupregistries HULKS <============: ", startup_nodes)
        else:    
            startup_nodes = startup_nodes_thors
            print("==========> Testing dedupregistries THORS <============: ", startup_nodes)
        
    
#         for ip in dedupregistries:
#             addr = ip.split(':')[0]
#             redisservers.append(addr+':7000')
#             redisservers.append(addr+':7001')
#         print redisservers   
#         rediscli_dbrecipe = StrictRedisCluster(startup_nodes=redisservers, decode_responses=True)


    



