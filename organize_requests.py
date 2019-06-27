
import sys
#import socket
import os
import json

####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren
#1 process the blob/layers 2 interpret each request/trace into http request form, then write out the results into a single "*-realblob.json" file
def match(realblob_location_files, trace_files, limit, getonly):
    
    print realblob_location_files, trace_files

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

    for trace_file in trace_files:
        print 'trace file: ' + trace_file
        with open(trace_file, 'r') as f:
            requests = json.load(f)
            #print 'request count: ' + str(len(requests))

        ret = []  
        fcnt = 0
          
        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']
            if len(uri.split('/')) < 3:
                continue
            #only interested in GET/pull PUT/push requests
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):# we only map layers not manifest; ('manifest' in uri) or 
                layer_id = uri.rsplit('/', 1)[1]#dict[-1] == trailing
                size = request['http.response.written']
                if size > 0:
            	    if 'PUT' == method and True == getonly:
            		continue
                    if count >= limit:
                        break

                    if i < len(blob_locations):
                        if 'manifest' in uri:# NOT SURE if a proceeding manifest
                            #if uri['manifest'] == 'manifest': what is this?
                                #create a fake blob with same size
                                #to the same dir as first valid blob file 
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
                            "http.request.uri": request['http.request.uri'],
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
            fname = os.path.basename(trace_file)
            with open(realblobtrace_dir+fname+'-realblob.json', 'w') as fp:
                json.dump(ret, fp)      

    print 'total unique layer count: ' + str(len(lTOblobdic))
    print 'total requests: ' + str(count) 
    print 'unique layer dataset size: ' + str(uniq_layerdataset_size)     

######
# NANNAN: realblobtrace_dir+'input_tracefile'+'-realblob.json'
######
####
# Random match
# the output file is the last trace filename-realblob.json, which is total trace file.
####
##########annotation by keren
#1 process the blob/layers 2 interpret each request/trace into http request form, then write out the results into a single "*-realblob.json" file
def fix_put_id(realblob_location_files, trace_files, limit, getonly):
    
    print trace_files
    
    layeridmap = {}
    i = 0
    count = 0
    put_reqs = 0
    find_puts = 0

    for trace_file in trace_files:
        print 'trace file: ' + trace_file
        with open(trace_file, 'r') as f:
            requests = json.load(f)
            #print 'request count: ' + str(len(requests))

        for request in requests:
            method = request['http.request.method']
            uri = request['http.request.uri']
	    #print uri
            if len(uri.split('/')) < 5:
                continue
            #only interested in GET/pull PUT/push requests
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):# we only map layers not manifest; ('manifest' in uri) or 
                size = request['http.response.written']
		#print uri
                if size > 0:
                    if count >= limit:
                        break

                    if i < 2*limit:    #len(blob_locations):
                        if 'GET' == method:
                            parts = uri.split('/')
                            reponame = parts[1] + '/' + parts[2] 
                            newid = reponame + '/' + str(size)
                            try:
                                newuri = layeridmap[newid]
                                if newuri == 0:
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
				#print newid
                            except Exception as e:
				#print newid
                                layeridmap[newid] = 0
				put_reqs += 1
                        
                        count += 1
                        #fcnt += 1
    
    print 'total requests: ' + str(count) 
    print 'total put requests: ' + str(put_reqs)
    print 'match put and get requests: ' + str(find_puts)   
    print 'total uniq put requests: ' + str(len(layeridmap))    
#     if fcnt:
#         for r in ret:
#             if 'PUT' == request['http.request.method']:
#                 uri = r['http.request.uri']
#                 parts = uri.split('/')
#                 reponame = parts[1] + '/' + parts[2] 
#                 newid = reponame + '/' + str(size)
#                 put_reqs += 1
#                 try: 
#                     newuri = layeridmap[newid]
#                     r['http.request.uri'] = newuri
#                     find_puts += 1
#                 except Exception as e:
#                     print "didn't find uri for this PUT req: "+uri
#                     pass
#         
#         fname = os.path.basename(trace_file)
#         with open(realblobtrace_dir+'input_tracefile'+'-realblob.json', 'w') as fp:
#             json.dump(ret, fp)      

#     print 'total unique layer count: ' + str(len(lTOblobdic))
    
#     print 'unique layer dataset size: ' + str(uniq_layerdataset_size)  
    
   

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
