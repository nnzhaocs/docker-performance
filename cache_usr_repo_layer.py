import time
import pdb
import datetime
from lru import LRU
import json
from Tkconstants import LAST

type = 'layer'
num_usrs = 9997
num_repos = 40264
num_layers = 829202

outputfile = 'hit_ratio_'+type+'.json'
    
class complex_cache:
    def __init__(self, size, type): # the number of items
        self.size = size # actual size of the cache
        self.lru = LRU(size)
        self.layerlru = LRU(size)

        self.hits = 0.0
        self.reqs = 0.0
        self.cache_stack_size = 0 # how much of the cache is occupied
        
        self.layermap = {}
        self.usrmap = {}
        self.manifestmap = {}
        
#         self.getmanifestreqs = 0
#         self.getlayerreqs = 0
#         self.putlayerreqs = 0
#         self.putmanifestreqs = 0
        
        self.manifestmiss = 0
        self.layermiss = 0
        
    def eviction(self):
#         if self.cache_stack_size + 1 > self.size: 
#             print "evict an item: "+str(self.lru.peek_last_item())
#             self.cache_stack_size -= 1
        found = False
        while self.cache_stack_size + 1 > self.size:    
            last = self.lru.peek_last_item()
            usrname = last[0]
            for l in reversed(self.layerlru.items()):
                if l[0] in self.usrmap[usrname]:
                    if len(self.layermap[l[0]]) == 1:
                        del self.layerlru[l[0]]
                        self.cache_stack_size -= 1
                        
#             for l in self.layerlru.items():
#                 if l[0] in self.usrmap[usrname]:
#                     found = True
#             if not found:
            del self.lru[last[0]]    
#         self.lru[request[2]] = 1
        
        
    def place(self, request):
        # request is a tuple (timestamp, layer, usrname, category)
        self.reqs += 1 
        usrname = request[2]
        layer = request[1]
        category = request[3]
#         if request['method'] == 'PUT':
#             if t = 'l':
#                 category = 'PUT layer'
#             else:
#                 category = 'PUT manifest'
#                 
#         elif request['method'] == 'GET':
#             if t = 'l':
#                 category = 'GET layer'
#             else:
#                 category = 'GET manifest'
                                
        if self.lru.has_key(usrname):             
            self.lru[usrname] = self.lru[usrname] + 1
        else:    
            self.lru[usrname] = 1
            
        if category == 'PUT manifest':
            manifestmap[layer] = 1
            
        if category == 'PUT layer':
            self.layerlru[layer] = 1
            layermap[layer].append(usrname)
            usrmap[usrname].append(layer)
            checkEviction()
        elif category == 'GET manifest':
            if layer not in manifestmap.keys():
                self.manifestmiss += 1
            else:
                self.manifesthit += 1
                self.hits += 1 
        elif category == 'GET layer':
            if layer not in layermap.keys():
#                 category = 'Fetch on miss'
                if usrname not in layermap[layer]:
                    layermap[layer].append(usrname)
                if layer not in usrmap[usrname]:
                    usrmap[usrname].append(layer)
                self.layerlru[layer] = 1
                checkEviction()
                self.layermiss += 1
            else:
                                  
                self.layerhit += 1
                self.hits += 1
                self.layerlru[layer] += 1            
            

def reformat(indata, type):
    ret = []
    print "reformating: wait 2 hrs ..." 
    for item in indata: 
	#print item
	uri = item['http.request.uri']
	timestamp = item['timestamp']       
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name
        
        if 'blobs' in uri:
            t = 'l'
        elif 'manifests' in uri:
            t = 'm'
        else:
            continue
        
        method = request['http.request.method']
        if request['method'] == 'PUT':
            if t = 'l':
                category = 'PUT layer'
            else:
                category = 'PUT manifest'
                
        elif request['method'] == 'GET':
            if t = 'l':
                category = 'GET layer'
            else:
                category = 'GET manifest'
        
        if type == 'layer':
#             if 'manifests' in uri:
#                 continue
            layer = uri.split('/')[-1]
            ret.append((timestamp, layer, usrname, category)) # delay: datetime
            
        elif type == 'repo':
            ret.append((timestamp, repo_name)) # delay: datetime
        elif type == 'usr':
	    #print timestamp+','+usrname
            ret.append((timestamp, usrname)) # delay: datetime

    return ret

# 5%, 10%, 15%, 20%, 25%, 30%, 40%, 50%
# usrs: 9,997 
# repos: 40,264
# layers: 829,202

def run_sim(requests, type):
    t = time.time()
       
    size1 = int(num_usrs * 0.05)
    size2 = int(num_usrs * 0.1)
    size3 = int(num_usrs * 0.15)
    size4 = int(num_usrs * 0.2)
    
    caches = []
    caches.append(complex_cache(size1, type))
    caches.append(complex_cache(size2, type))
    caches.append(complex_cache(size3, type))
    caches.append(complex_cache(size4, type))
    
    i = 0
    count = 10
    j = 0
    hr_no = 0
    hit_ratio_each_hr = {}
    
    for request in requests:
        j += 1
        if j == 1:
            starttime = request[0]
            print "starttime: "+str(starttime)
	#timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
	curtime= datetime.datetime.strptime(request[0], '%Y-%m-%dT%H:%M:%S.%fZ')
	initime = datetime.datetime.strptime(starttime, '%Y-%m-%dT%H:%M:%S.%fZ')
	interval = int((curtime - initime).total_seconds()) #% (60*60)
        for c in caches:
            c.place(request)
        #if interval > 1 and interval % (60 * 60) == 0:
            #pdb breakpoint here
            #pdb.set_trace()
        if interval > 1 and interval % (60*60) == 0: # calculate for each hr
            hr_no = interval/(60*60)
            
            hit_ratio_each_hr[str(hr_no) + ' 5% hit ratio'] = caches[0].hits/caches[0].reqs
            hit_ratio_each_hr[str(hr_no) + ' 10% hit ratio'] = caches[1].hits/caches[1].reqs
            hit_ratio_each_hr[str(hr_no) + ' 15% hit ratio'] = caches[2].hits/caches[2].reqs
            hit_ratio_each_hr[str(hr_no) + ' 20% hit ratio'] = caches[3].hits/caches[3].reqs
            
            print "5% hit ratio"+str(hit_ratio_each_hr[str(hr_no) + ' 5% hit ratio'])
            print "10% hit ratio"+str(hit_ratio_each_hr[str(hr_no) + ' 10% hit ratio'])
            print "15% hit ratio"+str(hit_ratio_each_hr[str(hr_no) + ' 15% hit ratio'])
            print "20% hit ratio"+str(hit_ratio_each_hr[str(hr_no) + ' 20% hit ratio'])
                
        if 1.*i / len(requests) > 0.1:
            i = 0
            print str(count) + '% done'
            count += 10
        i += 1

    return hit_ratio_each_hr


def init(data):

    print 'running cache simulation for: '+type
    #print data
    parsed_data = reformat(data, type)
    info = run_sim(parsed_data, type)
    
    with open(outputfile, 'w') as fp:
        json.dump(info, fp)

#     for thing in info:
#         print thing + ': ' + str(info[thing])

