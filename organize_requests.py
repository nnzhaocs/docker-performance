
import sys
#import socket
import os
import json
from audioop import avg
import random
####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren
#1 process the blob/layers 2 interpret each request/trace into http request form, then write out the results into a single "*-realblob.json" file

realblobtrace_dir = "/home/nannan/testing/realblobtraces/"

def match(realblob_location_files, tracedata, limit, getonly, layeridmap):
    
    print realblob_location_files #, trace_files

    blob_locations = []
    lTOblobdic = {}
        
    i = 0
    count = 0
    uniq_layerdataset_size = 0
    
    for realblob_location_file in realblob_location_files:
        print "File: "+realblob_location_file+" has the following blobs"
    
        with open(realblob_location_file, 'r') as f:
            for line in f:
                #print line
                if line:
                    blob_locations.append(line.replace("\n", ""))
    #print 'blob locations count: ' + str(len(blob_locations))

    ret = []  
    fcnt = 0
    put_reqs = 0
    find_puts = 0
    not_refered_put = 0
  
    for request in tracedata:
        method = request['http.request.method']
        uri = request['http.request.uri']
#         print uri
        size = request['http.response.written']
        
        if 'PUT' == method and True == getonly:
            continue
        
        if 'PUT' == method:
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            put_reqs += 1
            try: 
                newuri = layeridmap[newid]
                if newuri != '':
                    uri = newuri
                else:
                    not_refered_put += 0
            except Exception as e:
                print "######## didn't find get uri for this PUT req: "+uri+', '+newid
                continue
    	else:
            parts = uri.split('/')
            reponame = parts[1] + '/' + parts[2] 
            newid = reponame + '/' + str(size)
            try:
                newuri = layeridmap[newid]               
                find_puts += 1
            except Exception as e:
                pass
	    
        layer_id = uri.rsplit('/', 1)[1] #dict[-1] == trailing

        if i < len(blob_locations):
            if 'manifest' in uri:# NOT SURE if a proceeding manifest
                blob = None
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
    if fcnt:
        #fname = os.path.basename(trace_file)
        with open(realblobtrace_dir+'input_tracefile'+'-realblob.json', 'w') as fp:
            json.dump(ret, fp)      

    print 'total unique layer count: ' + str(len(lTOblobdic))
    print 'total requests: ' + str(count) 
    print 'unique layer dataset size: ' + str(uniq_layerdataset_size/1024/1024/1024) + ' GB'
    print 'total put requests: ' + str(put_reqs)
    print 'match put and get requests: ' + str(find_puts)   
    print 'put but no following get reqs: ' + str(not_refered_put)
    print 'total uniq put requests: ' + str(len(layeridmap))      


def extract_client_reqs(trace_files, clients, limit):
    print trace_files
    
    layeridmap = {}
    count = 0
    ret = []
    
    clireqmap = {}
    avgreqs = limit/clients
    choseclimap = {}
    chosesum = 0

    if not os.path.exists(os.path.join(realblobtrace_dir, os.path.basename(trace_files[-1])+'-client2reqcntdic.lst')):
	print "File: " + os.path.join(realblobtrace_dir, os.path.basename(trace_files[-1])+'-client2reqcntdic.lst') + " is not exists"
	print "Take few minutes to generate ........"
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
                    
                    cliaddr = request['http.request.remoteaddr']
                    try:
                        cnt = clireqmap[cliaddr]
                        clireqmap[cliaddr] += 1
                    except Exception as e:
                        clireqmap[cliaddr] = 1
       
        print 'total client count: ' + str(len(clireqmap))
        for i, value in sorted(clireqmap.items(), key=lambda kv: kv[1], reverse=True):
            print((i, value))                
        with open(os.path.join(realblobtrace_dir, os.path.basename(trace_files[-1])+'-client2reqcntdic.lst'), 'w') as fp:
    	    json.dump(clireqmap, fp)
    else:
	print "File: " + os.path.join(realblobtrace_dir, os.path.basename(trace_files[-1])+'-client2reqcntdic.lst') + " is already exists"
	with open(os.path.join(realblobtrace_dir, os.path.basename(trace_files[-1])+'-client2reqcntdic.lst'), 'r') as fp:
	    clireqmap = json.load(fp)
    
    #while chosesum < limit or chosesum > limit + 600:
    	
    randkeys = random.sample(clireqmap.keys(), clients)
    chosesum = 0
    for i in randkeys:
        chosesum += clireqmap[i]

    print 'total chosen client requsts: ' + str(chosesum)
    for i in randkeys:
	choseclimap[i] = clireqmap[i]
    print 'total chosen clients: ' + str(len(choseclimap))
    for i, value in sorted(choseclimap.items(), key=lambda kv: kv[1], reverse=True):
        print((i, value))
    
    return choseclimap
######
# NANNAN: realblobtrace_dir+'input_tracefile'+'-realblob.json'
######
####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren
#1 process the blob/layers 2 interpret each request/trace into http request form, then write out the results into a single "*-realblob.json" file
def fix_put_id(realblob_location_files, trace_files, limit, getonly, choseclimap):
    
    print trace_files
    
    layeridmap = {}
    i = 0
    count = 0
    put_reqs = 0
    find_puts = 0
    ret = []
    cntcli = 0
    newcli = {}

    for trace_file in trace_files:
        print 'trace file: ' + trace_file
        with open(trace_file, 'r') as f:
            requests = json.load(f)

        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']
	    cli = request['http.request.remoteaddr']
	    try:
		tmpcnt = choseclimap[cli] 
	    except Exception as e:
		continue
	    try: 
		tmpcnt = newcli[cli]
		newcli[cli] += 1
	    except Exception as e:
		newcli[cli] = 1
		cntcli += 1
            
            if len(uri.split('/')) < 5:
                continue

            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):# we only map layers not manifest; ('manifest' in uri) or 
                size = request['http.response.written']

                if size <= 0:
                    continue
                if count >= limit:
                    break

                if 'GET' == method:
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
                else:
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
#                             'data': blob
                    }
                ret.append(r)
                count += 1

    for i, value in sorted(newcli.items(), key=lambda kv: kv[1], reverse=True):
        print((i, value))

    print 'total requests: ' + str(count) 
    print 'total put requests: ' + str(put_reqs)
    print 'match put and get requests: ' + str(find_puts)   
    print 'total uniq put requests: ' + str(len(layeridmap))    
    print 'total num of clients: ' + str(len(newcli))
    #newcli = {}))
    return ret, layeridmap


######
# NANNAN: realblobtrace_dir+'input_tracefile'+'-realblob.json': gathering all the requests from trace files
######
def get_requests(files, t, limit):
    ret = []
    requests = []
    
    try:
        with open(realblobtrace_dir+'input_tracefile'+'-realblob.json', 'r') as f:
            requests.extend(json.load(f))#append a file
    except Exception as e:
        print('get_requests: Ignore this exception because no *-realblob file generated for this trace', e)
    
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
    print ("total number of replay requests are: ", totalcnt)
    return organized
