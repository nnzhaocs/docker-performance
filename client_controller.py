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
from rediscluster import StrictRedisCluster

def pull_from_registry(dgst, tup, type):       
    registry_tmp = tup[0]
    newreponame = tup[1] 
    print("tup, registry_tmp: ", tup, registry_tmp)
    result = {}
    size = 0
    global Testmode

    if (":5001" not in registry_tmp) and (":5000" not in registry_tmp):
        registry_tmp = registry_tmp+":5000"
    #print "layer/manifest: "+dgst+" goest to registry: "+registry_tmp
    onTime = 'yes'    

    dxf = DXF(registry_tmp, newreponame.lower(), insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
    #print("newreponame: ", newreponame)   
    #print("pull layer from registry, dgst: ", dgst)
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
    
    #print("pull: ", result)
    return result


def push_to_registry(blobfname, tup):    
    
    registry = tup[0]
    newreponame = tup[1]
    print tup
    onTime = 'yes'
    dxf = DXF(registry, newreponame.lower(), insecure=True) #DXF(registry_tmp, 'test_repo', insecure=True)
    
    try:
        dgst = dxf.push_blob(blobfname)
    except Exception as e:
            print("PUT/WARMUP: dxf object: ", dxf, "file: ", blobfname, e)
            dgst = 'bad'
            onTime = 'failed: '+str(e)  
    #print("push layer to registry, dgst: ", dgst)        
    result = {'registry': registry, 'onTime': onTime, 'dgst': dgst}                           

    #print result  
    return result


def get_write_registries(r, dedupreponame, nodedupreponame):
    global ring
    global ringdedup
    
    global Testmode
    global replica_level
     
    global siftmode
    global hotratio
    global nondedupreplicas
    global restorering
    global hotlayers
         
    uri = r['uri']
    id = uri.split('/')[-1]
    
    # *************** registry_tmps: [x, x, dedup] ************  
    registry_tmps = []
#     ptargenodes = []

    if ('manifest' in r['uri']) or (Testmode == 'nodedup') or (Testmode == 'primary'): 
        noderange = ring.range(id, replica_level, True)
        name = ''
        if Testmode == 'nodedup':
            name = nodedupreponame
        else:
            name = dedupreponame
        for i in noderange:
#<<<<<<< HEAD
                registry_tmps.append((i['nodename'], name))
       
#=======
#                registry_tmps.append((i['nodename'], nodedupreponame))
#>>>>>>> 4bd69a931154505fb637b556613fb6fedf57668f
    #ringdedup is backend
    #primary is registry
    elif Testmode == 'sift': 
        if replica_level == 1:
            #======= send to dedup ring =====#
            #
            registry_tmps.append((ringdedup.get_node(id), dedupreponame))            
        else:
            deduprange = ringdedup.range(id, replica_level, True)
            for i in deduprange:
                registry_tmps.append((i['nodename'], dedupreponame))
    return registry_tmps 


def get_read_registries(r, dedupreponame, nodedupreponame, backend):
    global ring
    global ringdedup
    
    global Testmode
    global replica_level
      
    global siftmode
    global hotratio
    global nondedupreplicas
     
    global hotlayers
       
    uri = r['uri']
    layer_id = uri.split('/')[-1] #(r['method'] == 'PUT') or 
    
    registry_tmps = []
    if (Testmode == 'nodedup')or (Testmode == 'primary') or ('manifest' in r['uri']): 
        registry_tmps = get_write_registries(r, dedupreponame, nodedupreponame)
        registry_tmp = random.choice(registry_tmps) 
       
        #print "layer: "+layer_id+"goest to registry: "+registry_tmp
        # registry_tmp is a tup
        return [registry_tmp]
    elif Testmode == 'restore':
        dgst = r['blob'] 
        registry_tmp = redis_stat_recipe_serverips(dgst)
        #print"GET: ips retrieved from redis for blob "+dgst+" is "+str(serverIps)
        if not registry_tmp:
            registry_tmp = ringdedup.get_node(layer_id)
        return [(registry_tmp, dedupreponame)]
    elif Testmode == 'sift':
        if backend:
            registry_tmps = get_write_registries(r, dedupreponame, nodedupreponame)
            registry_tmp = random.choice(registry_tmps)
        else:
            registry_tmp = ring.get_node(layer_id)
        #if 'standard' == siftmode:
        #    registry_tmp = random.choice(registry_tmps[:nondedupreplicas])
        #if 'selective' == siftmode:
        #    if layer_id in hotlayers:
        #        registry_tmp = random.choice(registry_tmps)
        #    else:
        #        registry_tmp = registry_tmps[0] #random.choice(registry_tmps[-(replica_level-1)])
        return [(registry_tmp, dedupreponame)] 


def redis_stat_recipe_serverips(dgst):
    global rediscli_dbrecipe
    
    key = "Layer:Recipe::"+dgst    
    if not rediscli_dbrecipe.exists(key):
        print "################ cannot find recipe for redis_stat_recipe_serverips ############" + dgst
        return None
    recipe = json.loads(rediscli_dbrecipe.execute_command('GET', key))
    serverIps = []
   
    return serverIps.append(recipe['MasterIp']) 


def redis_stat_rlmap(reponame):
    global rediscli_dbrecipe
    
    key = "RLMap::"+reponame 
    if not rediscli_dbrecipe.exists(key):
        print "################ cannot find rlmap for redis_stat_rlmap ############" + reponame
        return None 
    rlentry = json.loads(rediscli_dbrecipe.execute_command('GET', key))
    return rlentry


def redis_set_recipe_serverips(dgst, registries):
    global rediscli_dbrecipe
    
    key = "Layer:Recipe::"+dgst 
    des = {
        "HostServerIps": registries,
        }   
    rediscli_dbrecipe.execute_command('SET', key, json.dumps(des))
    return 
# type RLmapEntry struct {
#     Dgstmap map[digest.Digest]int64
#     //Dgstlst []digest.Digest
#     //Pullcnt int64
# }
def redis_set_rlmap(reponame, rlentry):
    global rediscli_dbrecipe
    
    key = "RLMap::"+reponame 
#     des = {
#         "Dgstmap": rlentry,
#         }   
    rediscli_dbrecipe.execute_command('SET', key, json.dumps(rlentry))
    return     


def get_request_registries(r, backend):
    registry_tmps = []

    uri = r['uri']
    parts = uri.split('/')
    reponame = parts[1] + parts[2]
    client = r['client']

    if 'manifest' in uri:
        type = 'MANIFEST'
        #print "put manifest request: "
    else:
        type = 'LAYER'
        #print "put layer request: "
#     elif tp == 'WARMUP':
#         type = 'WARMUPLAYER'

    dedupreponame = 'TYPE'+type+'USRADDR'+client+'REPONAME'+reponame
    nodedupreponame = "testrepo"
                                                    
    if 'GET' == r['method']:
        registry_tmps = get_read_registries(r, dedupreponame, nodedupreponame, backend)
    elif 'PUT' == r['method']:
        registry_tmps = get_write_registries(r, dedupreponame, nodedupreponame)
        
    return registry_tmps
          

def get_request(request):
    #print request
    print("request: ", request)
    results = []
    #print "get_request: dgst"
    dgst = request['blob']
    #print "dgst: "+dgst
    registries = []
    backend = False

    registries.extend(get_request_registries(request, backend))
    if len(registries) == 0:
        print "get_manifest_request ERROR no registry ######################## "+dgst
        return {}
    
    t = ''
    if 'manifest' in request['uri']:
        t = 'MANIFEST'
        #print "get manifest request: "
    else:
        t = 'LAYER'  
        #print "get layer requests: "
             
    result = pull_from_registry(dgst, registries[0], t)
    if 'failed:' in result['onTime']:
        backend = True
        registries = []
        registries.extend(get_request_registries(request, backend))
        result = pull_from_registry(dgst, registries[0], t)
    print("get_request: ", result)
    results.append(result)
    return results

def put_request(request):
    print("request: ", request)
    results = []
    registries = []
    registries.extend(get_request_registries(request))
    result = distribute_put_requests(request, 'PUT', registries)
    print("put_request: ", result)
    results.append(result)
    return results    
        
def distribute_put_requests(request, tp, registries):
    #print len(registries)
    all = {}
    trace = {}
    
    size = request['size']
    uri = request['uri']
#     parts = uri.split('/')
#     reponame = parts[1] + parts[2]
#     client = request['client']
    id = uri.split('/')[-1]
    
    newreponame = ''
    dgst = ''
    
    result = {}
    onTime = 'yes'
    
    global Testmode

    if 'manifest' in uri:
        type = 'MANIFEST'
        #print "put manifest request: "
    elif tp == 'PUT':
        type = 'LAYER'
        #print "put layer request: "
    elif tp == 'WARMUP':
        type = 'WARMUPLAYER'
        #print "warmup layer request: "
    
    blobfname = ''
    #manifest: randomly generate some files
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
        futures = [executor.submit(push_to_registry, blobfname, registry) for registry in registries]
        for future in futures:#.as_completed(timeout=60):
            #print("get_slice_request: future result: ", future.result(timeout=60))
            try:
                x = future.result()
                if 'failed' in x['onTime']:
                    onTime = x['onTime']
                else:
                    dgst = x['dgst']

            except Exception as e:
                print('distribute_put_requests: something generated an exception: %s', e, uri)   

    t = time.time() - now
       
    clear_extracting_dir(str(os.getpid()))
    
    if 'manifest' in uri and tp == 'WARMUP':
        tpp = 'warmupmanifest'          
    elif 'WARMUPLAYER' == type:
        tpp = 'warmuplayer'
        
    targenodes = [] 
    if 'manifest' not in uri: 
        if Testmode == 'sift' or Testmode == 'primary':       
            for tup in registries:
                registry_tmp = tup[0]
                targenodes.append(registry_tmp)
            redis_set_recipe_serverips(dgst, targenodes)  
        
    if 'WARMUP' == tp:    
        result = {'time': now, 'size': request['size'], 'onTime': onTime, 'duration': t, 'type': tpp}
        #print result
        trace[type+id] = dgst
        #print dgst
        all = {'trace': trace, 'result': result}
        return all    
    elif 'PUT' == tp:
        if 'manifest' not in uri:
            result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHLAYER'}
    	else:
    	    result = {'time': now, 'duration': t, 'onTime': onTime, 'size': size, 'type': 'PUSHMANIFEST'}
    	#print("push: ", blobfname, result)
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
    result = []

    for r in requests:
        i += 1
        if print_cnt == i:
            print ("==============> processed ", i*1.0/totalcnt, " requests! <=============", totalcnt) 
        if 'manifest' in r['uri']:
            pass
        else:
            if True == Wait: # and r['sleep'] > prev:
                time.sleep(1)
            #print "sleeping .... .... " + str(r['sleep'] - prev) + '/' + str(Accelerater)
            #time.sleep((r['sleep'] - prev)/Accelerater)
            
        if 'GET' == r['method']:
            #print "get repo request: "
            result = get_request(r)
            if result == None:
                print "empty: get"
                print r
        elif 'PUT' == r['method']:
            #print "push repo request: "
            result = put_request(r)
            if result == None:
                print "empty: put"
                print r
	else:
	    print "############# norecognized method #########"
	    print r['method']

        results_all.extend(result) 
        prev = result[0]['duration']

    return  results_all    

# type RLmapEntry struct {
#     Dgstmap map[digest.Digest]int64
#     //Dgstlst []digest.Digest
#     //Pullcnt int64
# }

def setup_rlmaps(requests):
    
#     repoldict = {}
    
    change = False 
    for r in requests:
        if 'manifest' in r['uri']:
            pass
	if 'GET' != r['method']:
	    pass
        else:
            uri = r['uri']
            parts = uri.split('/')
            reponame = parts[1] + parts[2]
#             id = uri.split('/')[-1]
#             client = r['client']
            dgst = r['blob']

            rlmapentry = redis_stat_rlmap(reponame)
            if rlmapentry != None:
                try:
                    x = rlmapentry['Dgstmap'][dgst]
                except:
                    change = True
                    rlmapentry['Dgstmap'][dgst] = 1
            else:
                change = True
                rlmapentry = {}
                rlmapentry['Dgstmap'] = {}
                rlmapentry['Dgstmap'][dgst] = 1
                        
            if change:
                print rlmapentry
                redis_set_rlmap(reponame, rlmapentry)        
    
    
def config_client(ring_input, ringdedup_input, primaryregistries, dedupregistries, hotlayers_input, testmode, wait, accelerater, replica_level_input, siftmode_input, nondedupreplicas_input): 

    global rediscli_dbrecipe
    global rjpool_dbNoBFRecipe

    global Testmode
    global Wait
    global Accelerater
    global replica_level
    
    global ring  
    global ringdedup
    global hotlayers
    global siftmode
    global nondedupreplicas

    global restorering

    nondedupreplicas = nondedupreplicas_input
    siftmode = siftmode_input
    ring = ring_input
    ringdedup = ringdedup_input
    hotlayers = hotlayers_input
        
    Testmode = testmode
    Wait = wait
    Accelerater = accelerater
    replica_level = replica_level_input
    #startupnodes = []

    print("The testmode is: ", Testmode)
    print("The replica_level is: ", replica_level)
    print("The Wait is: ", Wait)
    print("The Accelerater is: ", Accelerater)

    restoreregistries=[]
    print("===========> Testing dedupregistries <============", dedupregistries)
    if Testmode == 'restore':
        for registry in dedupregistries:
            ip = registry.split(':')[0]
            print ip
            restoreregistry = ip+":5001"
            restoreregistries.append(restoreregistry)
        print restoreregistries
        restorering = HashRing(nodes = restoreregistries)

    if Testmode != 'nodedup':
        if not len(dedupregistries):
            registries = primaryregistries
        else:
            registries = dedupregistries
        if "192.168.0.17" in registries[0]:
            startupnodes = startup_nodes_hulks
            print("==========> Testing dedupregistries HULKS <============: ", startupnodes)
        else:    
            startupnodes = startup_nodes_thors
            print("==========> Testing dedupregistries THORS <============: ", startupnodes)
      
        rediscli_dbrecipe = StrictRedisCluster(startup_nodes=startupnodes, decode_responses=True)


    



