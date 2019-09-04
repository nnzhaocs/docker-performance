
import sys
#import socket
import os
import json
from audioop import avg, reverse
import random
import datetime
import math
from collections import defaultdict
from utilities import *
####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren
#1 process the blob/layers 2 interpret each request/trace into http request form, then write out the results into a single "*-realblob.json" file

realblobtrace_dir = "/home/nannan/testing/realblobtraces/"


def sampleLayers(realblob_location_files, tracedata, layeridmap):
    print "sampling ... "
    print realblob_location_files #, trace_files
    layerdict = {}
    blob_locations = []
  
    for realblob_location_file in realblob_location_files:
        print "File: "+realblob_location_file+" has the following blobs"
    
        with open(realblob_location_file, 'r') as f:
            for line in f:
                if line:
                    blob_locations.append(line.replace("\n", ""))
  
    for request in tracedata:
        method = request['http.request.method']
        uri = request['http.request.uri']
	size = request['http.response.written']
        if 'GET' == method and 'manifest' in uri:
            pass       
        elif 'PUT' == method and 'blobs' in uri:
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            try: 
                newuri = layeridmap[newid]
                if newuri != '':
                    uri = newuri
                else:
                    pass
            except Exception as e:
                print "######## didn't find get uri for this PUT req: "+uri+', '+newid
                continue
        elif 'GET' == method and 'blobs' in uri:            
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            try:
                newuri = layeridmap[newid]               
            except Exception as e:
                pass
        elif 'PUT' == method and 'manifest' in uri:
            pass
        else:
            print request
        
        layer_id = uri.rsplit('/', 1)[1] #dict[-1] == trailing
        if 'manifest' in uri:
            pass
        else:
            try:
                x = layerdict[layer_id]
            except Exception as e:
                layerdict[layer_id] = 1
    
    print "the number of uniq layers are: "+str(len(layerdict))
    layersamples = random.sample(blob_locations, len(layerdict))
    with open(realblobtrace_dir+'input_tracefile'+'-layers.lst', 'w') as fp:
        for l in layersamples:
            fp.write(l+'\n')
    return layersamples

def match(realblob_location_files, tracedata, layeridmap):
    print "match ... "
    print realblob_location_files #, trace_files

    blob_locations = sampleLayers(realblob_location_files, tracedata, layeridmap)
    lTOblobdic = {}
    mdic = {}
        
    i = 0
    count = 0
    uniq_layerdataset_size = 0
    
#     for realblob_location_file in realblob_location_files:
#         print "File: "+realblob_location_file+" has the following blobs"
#     
#         with open(realblob_location_file, 'r') as f:
#             for line in f:
#                 #print line
#                 if line:
#                     blob_locations.append(line.replace("\n", ""))
    #print 'blob locations count: ' + str(len(blob_locations))

    ret = []  
    fcnt = 0
    put_reqs = 0
    find_puts = 0
    not_refered_put = 0
    
    put_M = 0
    get_M = 0
    get_L = 0
    
    for request in tracedata:
        method = request['http.request.method']
        uri = request['http.request.uri']
#         print uri
        size = request['http.response.written']
        if 'GET' == method and 'manifest' in uri:
            get_M += 1
        
        elif 'PUT' == method and 'blobs' in uri:
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            put_reqs += 1
            try: 
                newuri = layeridmap[newid]
                if newuri != '':
                    uri = newuri
                else:
		    #uri = 'v2/'+reponame+'/'+blobs+uri.rsplit('/', 1)[1]+str(size)
                    not_refered_put += 1
            except Exception as e:
                print "######## didn't find get uri for this PUT req: "+uri+', '+newid
                continue
    	elif 'GET' == method and 'blobs' in uri:
            get_L += 1
            
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            try:
                newuri = layeridmap[newid]               
                find_puts += 1
            except Exception as e:
                pass
        elif 'PUT' == method and 'manifest' in uri:
            put_M += 1
            put_reqs += 1
        else:
            print request
	    
        layer_id = uri.rsplit('/', 1)[1] #dict[-1] == trailing

        if i < len(blob_locations):
            if 'manifest' in uri:# NOT SURE if a proceeding manifest
                blob = None
                try:
                    x = mdic[layer_id]
                except Exception as e:
                    mdic[layer_id] = 1
            else:
                try:
                    blob = lTOblobdic[layer_id]
                except Exception as e:     
                    blob = blob_locations[i] # temp record the blob
                    lTOblobdic[layer_id] = blob # mark blob as recorded
                    i += 1
                    size = os.stat(blob).st_size # record blob size
                    uniq_layerdataset_size += size
            # except size and data, others are same with original reqs
            r = {
                "host": request['host'],
                "http.request.duration": request['http.request.duration'],
                "http.request.method": request['http.request.method'],
                "http.request.remoteaddr": request['http.request.remoteaddr'],
                "http.request.uri": uri,
                "http.request.useragent": request['http.request.useragent'],
                "http.response.status": request['http.response.status'],
                "http.response.written": size,
                "id": request['id'],
                "timestamp": request['timestamp'],
                'data': blob
            }
            #print r
            ret.append(r)
            count += 1
            fcnt += 1

    ret.sort(key= lambda x: x['timestamp'])
    if fcnt:
        #fname = os.path.basename(trace_file)
        with open(realblobtrace_dir+'input_tracefile'+'-realblob.json', 'w') as fp:
            json.dump(ret, fp)      
        #pass

    start = datetime.datetime.strptime(ret[0]['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.datetime.strptime(ret[-1]['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
    
    print 'total requests: ' + str(count) 
    print 'total unique layer count: ' + str(len(lTOblobdic))
    print 'total unique manifest count: ' + str(len(mdic))
    print 'total uniq get layer requests: ' + str(get_L)   
    print 'total uniq get manifest requests: ' + str(get_M)     
    print 'total uniq put layer requests: ' + str(len(layeridmap))   
    print 'total uniq put manifest requests: ' + str(put_M)  
    print 'total replay time: '+ str((end-start).total_seconds()/60/60) +' Hr'
    print 'unique layer dataset size: %5.3f GB'%(float(uniq_layerdataset_size)/1024/1024/1024) 
               
    print 'total put requests: ' + str(put_reqs)
    print 'matched put and following get requests: ' + str(find_puts)   
    print 'put but no following get reqs: ' + str(not_refered_put)

######
# NANNAN: realblobtrace_dir+'input_tracefile'+'-realblob.json'
######
####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren

def fix_put_id(trace_files, limit):
    print "fix_put_id ... "
    print trace_files
    
    layeridmap = {}
    i = 0
    count = 0
    put_reqs = 0
    find_puts = 0
    ret = []
    manifestidmap = {} # put manifest request
    reputm = 0

    for trace_file in trace_files:
        print 'trace file: ' + trace_file
        with open(trace_file, 'r') as f:
            requests = json.load(f)
        
        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']

            if len(uri.split('/')) < 5:
                continue

            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):# we only map layers not manifest; ('manifest' in uri) or 
                size = request['http.response.written']

                if size <= 0:
                    continue
                if count >= limit:
                    break

                if 'PUT' == method and 'manifest' in uri:
                    # ***** remove same manifest ******
                    parts = uri.split('/')
                    manifest_id = uri.rsplit('/', 1)[1]
                    try:
                        x = manifestidmap[manifest_id]
                        reputm += 1
                        continue
                    except Exception as e:
                        manifestidmap[manifest_id] = 1
                elif 'GET' == method and 'blobs' in uri:
                    parts = uri.split('/')
                    reponame = parts[1] + '/' + parts[2] 
                    newid = reponame + '/' + str(size)
                    try:
                        newuri = layeridmap[newid]
                        if newuri == '':
                            layeridmap[newid] = uri				
                        find_puts += 1
                    except Exception as e:
                        pass
                elif 'PUT' == method and 'blobs' in uri:
                    parts = uri.split('/')
                    reponame = parts[1] + '/' + parts[2] 
                    newid = reponame + '/' + str(size)
                    try:
                        newuri = layeridmap[newid]
                        continue
                    except Exception as e:
                        layeridmap[newid] = ''
                        put_reqs += 1 
                        
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
                    }
                ret.append(r)
                count += 1

    #for i, value in sorted(newcli.items(), key=lambda kv: kv[1], reverse=True):
    #    print((i, value))

    print 'total requests: ' + str(count) 
    print 'total put requests: ' + str(put_reqs)
    print 'match put and get requests: ' + str(find_puts)   
    print 'total uniq put requests: ' + str(len(layeridmap))    
    return ret, layeridmap


######
# NANNAN: realblobtrace_dir+'input_tracefile'+'-realblob.json': gathering all the requests from trace files
######
def get_requests(fname):
    print "get_requests ... "
    ret = []
    requests = []
    
    try:
        with open(fname, 'r') as f:
            requests.extend(json.load(f))#append a file
    except Exception as e:
        print('##############: get_requests: ##############', e, fname)
    
    for request in requests: #load each request
        method = request['http.request.method']
        uri = request['http.request.uri']
        size = request['http.response.written']
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
    ret.sort(key= lambda x: x['delay']) # reorder by delay time

    return ret  


def get_hotlayers(requests, hotratio, clients):
    layeridtopop = {}
    selectedlayers = []
    for r in requests:
        uri = r['http.request.uri']
        if 'manifest' in r['http.request.uri']:
            continue
        layer_id = uri.rsplit('/', 1)[1]
        try:
            pop = layeridtopop[layer_id]
            layeridtopop[layer_id] += 1
        except Exception as e:
            layeridtopop[layer_id] = 1
    #print len(layeridtopop)        
    selected = len(layeridtopop) * hotratio 
    print('selected: ', selected)
    i = 0       
    for k, v in sorted(layeridtopop.items(), key=lambda item: item[1], reverse=True):
        #print("%s: %d" % (k, v))
        if i >= selected:
            break
        i += 1
        selectedlayers.append(k)
    
    fname = realblobtrace_dir+'input_tracefile'+'tmp_hotlayers.json'
    targetname = realblobtrace_dir+'input_tracefile'+'_hotlayers.json'
    with open(fname, 'w') as fp:
        json.dump(selectedlayers, fp)
    
    for clientaddr in clients:
        send_to_client(fname, clientaddr, targetname)    
    
            
##############
# NANNAN: old organize request function
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
def organize_and_send_clients(numclients, clients, hotratio):
    
    fname = realblobtrace_dir+'input_tracefile'+'-realblob.json'
    with open(fname, 'r') as f:
        requests = json.load(f) #append a file
    
    organized = [[] for x in xrange(numclients)]
    clientTOThreads = {}
    clientToReqs = defaultdict(list)
    threadsize = {x: 0 for x in range(0, numclients)}
     
    print "load number of replay requests: " + str(len(requests)) 
   
    for r in requests:           
        clientToReqs[r['http.request.remoteaddr']].append(r)
        
    get_hotlayers(requests, hotratio, clients)
        
    i = 0 
    for cli in sorted(clientToReqs, key=lambda k: len(clientToReqs[k]), reverse=True):
        try:
            threadid = clientTOThreads[cli]
            organized[threadid].extend(clientToReqs[cli])
            threadsize[threadid] += len(clientToReqs[cli])
        except Exception as e:
            i += 1
            threadid = min(threadsize, key=threadsize.get)
            organized[threadid].extend(clientToReqs[cli])
            clientTOThreads[cli] = threadid
            threadsize[threadid] += len(clientToReqs[cli])   
              
    print ("number of real clients:", i)      
    
    i = 0
    for clireqlst in organized:
        fname = realblobtrace_dir+'input_tracefile-'+clients[i]+'-realblob.json'
        targetname = realblobtrace_dir+'input_tracefile-'+'client-realblob.json'
        clientaddr = clients[i]
        
        print ("send to client: client, number reqs", clients[i], len(clireqlst))
        with open(fname, 'w') as fp:
            json.dump(clireqlst, fp)

        i = (i+1)%len(clients)
        
        send_to_client(fname, clientaddr, targetname)
                
    #print organized
    totalcnt = sum([len(x) for x in organized])
    print ("total number of replay requests are: ", totalcnt)
#     return organized


def organize(out_trace, numclients, clients):
    
    fname = realblobtrace_dir+'input_tracefile'+'-client-realblob.json' 
    requests = get_requests(fname)
    #print out_trace
    with open(out_trace, 'r') as f:
        blob = json.load(f)
    
    numclients = numclients/len(clients)
    organized = [[] for x in xrange(numclients)]
    clientTOThreads = {}
    clientToReqs = defaultdict(list)
    threadsize = {x: 0 for x in range(0,numclients)}
    
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
        id = r['uri'].split('/')[-1]
        
        if 'manifest' in r['uri']:
            type = 'MANIFEST'
        else:
            type = 'WARMUPLAYER'
            
        if (type+id) in blob and 'GET' == r['method']:
            b = blob[type+id]
            #print "dgst: "+b
            if b != 'bad':
                request['blob'] = b # dgest
                request['method'] = 'GET'
        else:
            request['size'] = r['size']
            request['method'] = 'PUT'
        clientToReqs[r['client']].append(request)
    i = 0 
    for cli in sorted(clientToReqs, key=lambda k: len(clientToReqs[k]), reverse=True):
        try:
            threadid = clientTOThreads[cli]
            organized[threadid].extend(clientToReqs[cli])
            threadsize[threadid] += len(clientToReqs[cli])
        except Exception as e:
            i += 1
            threadid = min(threadsize, key=threadsize.get)
            organized[threadid].extend(clientToReqs[cli])
            clientTOThreads[cli] = threadid
            threadsize[threadid] += len(clientToReqs[cli])   
              
    print ("number of real clients:", i)      
     
#     for clireqlst in organized:
#         clireqlst.sort(key= lambda x: x['delay'])
#         print ("number of request for client:", i)
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
    
    totalcnt = sum([len(x) for x in organized])
    print ("total number of replay requests are: ", totalcnt)
    return organized
