import sys
import socket
import os
from argparse import ArgumentParser
import requests
import time
import datetime
import pdb
import random
import threading
import multiprocessing
import json 
import yaml
from dxf import *
from multiprocessing import Process, Queue
import importlib
import hash_ring
from mimify import repl

## get requests
def send_request_get(client, payload):
    ## Read from the queue
    s = requests.session()
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    s.post("http://" + str(client) + "/up", data=json.dumps(payload), headers=headers, timeout=100)

def send_warmup_thread(requests, q, registry):
    trace = {}
    dxf = DXF(registry, 'test_repo', insecure=True)
    for request in requests:
        if request['size'] < 0:
            trace[request['uri']] = 'bad'
        try:
            dgst = dxf.push_blob(request['data'])
        except Exception as e:
	    print("dxf send exception: ", e, request['data'])
            dgst = 'bad'
        print request['uri'], dgst
        trace[request['uri']] = dgst
    q.put(trace)

#######################
# send to registries according to cht 
# warmup output file is <uri to dgst > map table
# only consider 'get' requests
# let set threads = n* len(registries)
#######################

def warmup(data, out_trace, registries, threads, numclients):
    trace = {}
    processes = []
    q = Queue()
    process_data = []
    # nannan
    # requests distribution based cht, where digest is blob digest.
    # process_data = [[] [] [] [] [] [] [] ... []threads]
    #                 r1 r2 r3 r1 r2 r3
    
    ring = hash_ring.HashRing(registries)
    
    for i in range(threads):
        process_data.append([])

    count = 0
    for request in data:
        if request['method'] == 'GET':
            uri = request['uri']
            layer_id = uri.split('/')[-1]
            registry_tmp = ring.get_node(layer_id) # which registry should store this layer/manifest?
            idx = registries.index(registry_tmp) 
            process_data[(idx+(len(registries)*count))%threads].append(request)
            print "layer: "+layer_id+"goest to registry: "+registry_tmp+", idx:"+str(idx)
            count += 1
	    #if i > 10:
		#break;
    threadcount = 0
    for regidx in range(len(registries)):
        for i in range(0, threads, len(registries)):
            p = Process(target=send_warmup_thread, args=(process_data[regidx+i], q, registries[regidx]))
            processes.append(p)
            threadcount += 1

    for p in processes:
        p.start()

    for i in range(threads):
        d = q.get()
        for thing in d:
            if thing in trace:
                if trace[thing] == 'bad' and d[thing] != 'bad':
                    trace[thing] = d[thing]
            else:
                trace[thing] = d[thing]

    for p in processes:
        p.join()

    with open(out_trace, 'w') as f:
        json.dump(trace, f)
    print("total threads:", threadcount)


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
    wrongdigest = 0
    startTime = responses[0]['time']
    for r in responses:
	print r
#         if r['onTime'] == 'failed':
##nannan
        if isinstance(r['onTime_l'], list):
	    #i = [json.loads(l) for l in r['onTime_l']]
	    #print i
            for i in r['onTime_l']:
                if "failed" in i['onTime']:
                    total -= 1
                    failed += 1
                    break # no need to care the rest partial layer.
            	data += i['size']
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            #data += r['size']
#             if r['onTime'] == 'yes':
#                 onTimes += 1
#             if r['onTime'] == 'yes: wrong digest':
#                 wrongdigest += 1
        else:
            if "failed" in r['onTime']:
                total -= 1
                failed += 1
                continue
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            data += r['size']
#             if r['onTime'] == 'yes':
#                 onTimes += 1
##             if r['onTime'] == 'yes: wrong digest':
##                 wrongdigest += 1
            
    duration = endtime - startTime
    print 'Statistics'
    print 'Successful Requests: ' + str(total)
    print 'Failed Requests: ' + str(failed)
#     print 'Wrong digest requests: '+str(wrongdigest)
    print 'Duration: ' + str(duration)
    print 'Data Transfered: ' + str(data) + ' bytes'
    print 'Average Latency: ' + str(latency / total)
#     print '% requests on time: ' + str(1.*onTimes / total)
    print 'Throughput: ' + str(1.*total / duration) + ' requests/second'

           
def serve(port, ids, q, out_file):
    server_address = ("0.0.0.0", port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(server_address)
        sock.listen(len(ids))
    except:
        print "Port already in use: " + str(port)
        q.put('fail')
        quit()
    q.put('success')
 
    i = 0
    response = []
    print "server waiting"
    while i < len(ids):
        connection, client_address = sock.accept()
        resp = ''
        while True:
            r = connection.recv(1024)
            if not r:
                break
            resp += r
        connection.close()
        try:
            info = json.loads(resp)
            if info[0]['id'] in ids:
                info = info[1:]
                response.extend(info)
                i += 1
        except:
            print 'exception occured in server'
            pass

    with open(out_file, 'w') as f:
        json.dump(response, f)
    print 'results written to ' + out_file
    stats(response)

  
## Get blobs
def get_blobs(data, clients_list, port, out_file):
    processess = []

    ids = []
    for d in data:
        ids.append(d[0]['id'])

    serveq = Queue()
    server = Process(target=serve, args=(port, ids, serveq, out_file))
    server.start()
    status = serveq.get()
    if status == 'fail':
        quit()
    ## Lets start processes
    i = 0
    for client in clients_list:
        p1 = Process(target = send_request_get, args=(client, data[i], ))
        processess.append(p1)
        i += 1
        print "starting client ..."
    for p in processess:
        p.start()
    for p in processess:
        p.join()

    server.join()

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


def absoluteFilePaths(directory):
    absFNames = []
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            absFNames.append(os.path.abspath(os.path.join(dirpath, f)))
            
    return absFNames

####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####

def match(realblob_locations, trace_files):
    print realblob_locations, trace_files

    blob_locations = []
    tTOblobdic = {}
    blobTOtdic = {}
    ret = []
    i = 0
    
    for location in realblob_locations:
        absFNames = absoluteFilePaths(location)
	print "Dir: "+location+" has the following files"
	print absFNames
        blob_locations.extend(absFNames)
    
    for trace_file in trace_files:
        with open(trace_file, 'r') as f:
            requests = json.load(f)
            
        for request in requests:
            
            method = request['http.request.method']
            uri = request['http.request.uri']
	    if len(uri.split('/')) < 3:
		continue
            layer_id = uri.rsplit('/', 1)[1]
            usrname = uri.split('/')[1]
            repo_name = uri.split('/')[2]
            
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):
                size = request['http.response.written']
                if size > 0:
                    if i < len(blob_locations):
                        blob = blob_locations[i]
                        if layer_id in tTOblobdic.keys():
                            continue
                        if blob in blobTOtdic.keys():
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
                        i += 1
                               
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

def organize(requests, out_trace, numclients, client_threads, port, wait, registries, round_robin, push_rand, replay_limits):
    organized = []

    if round_robin is False:
        ring = hash_ring.HashRing(range(numclients))
    with open(out_trace, 'r') as f:
        blob = json.load(f)

    for i in range(numclients):
        organized.append([{'port': port, 'id': random.getrandbits(32), 'threads': client_threads, 'wait': wait, 'registry': registries, 'random': push_rand}])
        print organized[-1][0]['id']
    i = 0
    cnt = 0
    
    for r in requests:
        cnt += 1
        if replay_limits > 0:
            if cnt > replay_limits:
                break
        request = {
            'delay': r['delay'],
            'duration': r['duration'],
            'data': r['data'],
            'uri': r['uri']
        }
        if r['uri'] in blob:
            b = blob[r['uri']]
            if b != 'bad':
                request['blob'] = b # dgest
                request['method'] = 'GET'
                if round_robin is True:
                    organized[i % numclients].append(request)
                    i += 1
                else:
                    organized[ring.get_node(r['client'])].append(request)
        else:
            request['size'] = r['size']
            request['method'] = 'PUT'
            if round_robin is True:
                organized[i % numclients].append(request)
                i += 1
            else:
                organized[ring.get_node(r['client'])].append(request)

    return organized


def main():

    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    parser.add_argument('-p', '--port', dest='pppp', type=str, required=False, help = 'identifier')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, help= 'Trace player command. Possible commands: warmup, run, simulate, warmup is used to populate the registry with the layers of the trace, run replays the trace, and simulate is used to test different caching and prefecting policies.')

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

    if verbose:
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
            print exit(1)
    elif verbose:
        print 'limit_type not specified, entirety of trace files will be used will be used.'

    if 'output' in inputs['trace']:
        out_file = inputs['trace']['output']
    else:
        out_file = 'output.json'
        if verbose:
            print 'Output trace not specified, ./output.json will be used'

    generate_random = False
    if args.command != 'simulate':
        if "warmup" not in inputs or 'output' not in inputs['warmup']:
            print 'warmup not specified in config, warmup output required. Exiting'
            exit(1)
        else:
            interm = inputs['warmup']['output']
            if 'random' in inputs['warmup']:
                if inputs['warmup']['random'] is True:
                    generate_random = True

    registries = []
    if 'registry' in inputs:
        registries.extend(inputs['registry'])
     
    print(registries)
    #NANNAN
    if args.command == 'match':    
        if 'realblobs' in inputs['client_info']:
            realblob_locations = inputs['client_info']['realblobs']
            match(realblob_locations, trace_files)
            return
	else:
	    print "please write realblobs in the config files"
	    return

#     replay_limits = 0
#     if 'debugging' in inputs['client_info']:
#         if inputs['client_info']['debugging'] is True:
#             replay_limits = inputs['client_info']['debugging']['limits']

    json_data = get_requests(trace_files, limit_type, limit)

    if args.command == 'warmup':
        if verbose: 
            print 'warmup mode'
        if 'threads' in inputs['warmup']:
            threads = inputs['warmup']['threads']
        else:
            threads = 1
        if verbose:
            print 'warmup threads: ' + str(threads)
            # NANNAN: not sure why only warmup a single registry, let's warmup all.
        warmup(json_data, interm, registries, threads, generate_random)

    elif args.command == 'run':
        if verbose:
            print 'run mode'

        if 'client_info' not in inputs or inputs['client_info'] is None:
            print 'client_info required for run mode in config file'
            print 'exiting'
            exit(1)

        if 'master_port' not in inputs['client_info']:
            if verbose:
                print 'master server port not specified, assuming 8080'
                port = 8080
        else:
            port = inputs['client_info']['master_port']
            if verbose:
                print 'master port: ' + str(port)

        if 'threads' not in inputs['client_info']:
            if verbose:
                print 'client threads not specified, 1 thread will be used'
            client_threads = 1
        else:
            client_threads = inputs['client_info']['threads']
            if verbose:
                print str(client_threads) + ' client threads'

        if 'client_list' not in inputs['client_info']:
            print 'client_list entries are required in config file'
            exit(1)
        else:
            client_list = inputs['client_info']['client_list']

        if 'wait' not in inputs['client_info']:
            if verbose:
                print 'Wait not specified, clients will not wait'
            wait = False
        elif inputs['client_info']['wait'] is True:
            wait = True
        else:
            wait = False

        round_robin = True
        
        if 'route' in inputs['client_info']:
            if inputs['client_info']['route'] is True:
                round_robin = False

        data = organize(json_data, interm, len(client_list), client_threads, port, wait, registries, round_robin, generate_random, 0)
        ## Perform GET
        get_blobs(data, client_list, port, out_file)


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
