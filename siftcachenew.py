import datetime
from statistics import mean
import pdb
from collections import defaultdict
from lru import LRU

import json

dbNoUsrecipe = 4
dbNoReporecipe = 5 # repo with layer
dbNoMefrecipe = 6  # repo with manifests
dbNoLyrecipe = 7 # layers get client repo

#
# usr -> repoid 
# repo -> layerid
# layerid -> size

#
# repo we add a time.
#
#

        

class siftcache:

    def __init__(self, size, threshold):
#         self.repos = {}
#         self.manifest = {}
#         self.rtimeout = rtimeout
#         self.mtimeout = mtimeout
#         self.size = 0
#         self.usr_lru = []
#         self.size_list = []
#         self.goodprefetch = 0
#         self.badprefetch = 0
        
        
        self.size = size # actual size of the cache
        
        self.usr_lru = LRU(9997)
        self.repo_lru = LRU(40264)
        self.layer_lru = LRU(829202)
        self.free_buffer = size # init to cache size
        self.size_threshold = threshold # how close you can get to cache 
        self.layer_size_map = {}
        self.layer_usr_map = defaultdict(set)
        self.hit = 0
        self.miss = 0
        self.total_evictions = 0

        self.eviction_times =[]
        self.usrs_in_cache_over_time = []
        self.reqs = 0.0
        
        self.manifest_hit = 0
        self.layer_hit = 0
        
        self.layerbuffer_hit = 0
        self.filecache_hit = 0
#         self.fetchonmiss_hit = 0
#         self.superfetch = 0
        
#         self.putcache_size = 0
#         self.prefetch_hit = 0
        self.fetchonmiss_hit = 0
#         self.superfetch = 0
        
        # (layer_id, cache_type)
        # (manifest_id, cache_type)
        
        self.cache_stack_size = 0 # how much of the cache is occupied
        
    # def update_usermaplru(self, usr, repo, layer_id, manifest_id):
    #     if layer_id:



    def cacheeviction(self):
        self.usrs_in_cache_over_time.append(len(self.usr_lru.items()))
        while self.free_buffer < self.size_threshold:
            last_usr = self.usr_lru.peek_last_item()[0]
            reverse_layerlru_list = self.layer_lru.items()[::-1]
            for layerid, i_i in reverse_layerlru_list:
                if 'manifest' not in layerid and len(list(self.layer_usr_map[layerid])) == 1 and list(self.layer_usr_map[layerid])[0] == last_usr:
                    del self.layer_lru[layerid]
                    del self.layer_usr_map[layerid]
                    self.free_buffer += self.layer_size_map[layerid]
                    del self.layer_size_map[layerid]
                else:
                    self.layer_usr_map[layerid].discard(last_usr)
                self.total_evictions += 1
            del self.usr_lru[last_usr]
            self.eviction_times.append(self.free_buffer)
           
           

    def pushintocache(self, request):
        # print "space left in user cache: "+str(9997-len(self.usr_lru.items()))
        if self.layer_lru.has_key(request['id']):
            self.layer_lru[request['id']] = self.layer_lru[request['id']] + 1
            if self.usr_lru.has_key(request['client']):
                self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
            else:
                self.usr_lru[request['client']] = 1
            self.layer_usr_map[request['id']].add(request['client'])
        else:
            self.layer_lru[request['id']] = 1
            self.layer_size_map[request['id']] = request['size']
            self.layer_usr_map[request['id']].add(request['client'])
            if self.usr_lru.has_key(request['client']):
                self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
            else:
                self.usr_lru[request['client']] = 1
            self.free_buffer -= self.layer_size_map[request['id']]
        if self.free_buffer < self.size_threshold:
            self.cacheeviction()

    def pullfromcache(self, request):
        # print "space left in user cache: "+str(9997-len(self.usr_lru.items()))
        if self.layer_lru.has_key(request['id']):
            self.layer_lru[request['id']] = self.layer_lru[request['id']] + 1
            if self.usr_lru.has_key(request['client']):
                self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
            else:
                self.usr_lru[request['client']] = 1
            self.layer_usr_map[request['id']].add(request['client'])
            self.hit += 1
        else:
            self.miss += 1
            self.layer_lru[request['id']] = 1
            self.layer_size_map[request['id']] = request['size']
            self.layer_usr_map[request['id']].add(request['client'])
            if self.usr_lru.has_key(request['client']):
                self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
            else:
                self.usr_lru[request['client']] = 1
            self.free_buffer -= self.layer_size_map[request['id']]
        if self.free_buffer < self.size_threshold:
            self.cacheeviction()
        
        
    def put(self, request):
        if request['method'] == 'PUT': 
            self.pushintocache(request)
        elif request['method'] == 'GET':
            self.pullfromcache(request)

    def get_info(self):
        data = {
            'hits': self.hit,
            'misses': self.miss,
            'hit ratio': (self.hit*1.0)/(self.hit +self.miss),
            'cache size': self.size,
            'evictions over lifetime': self.total_evictions,
            'max users in cache': 9997-min(self.usrs_in_cache_over_time),
            'average users in cache': 9997-mean(self.usrs_in_cache_over_time)
            }
        return data

    def get_size_list(self):
        return self.size_list

def extract(data):
  
    requests = []

    for request in data:
        method = request['http.request.method']
        size = request['http.response.written']

        uri = request['http.request.uri']
        timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if 'blobs' in uri:
            t = 'l'
        elif 'manifests' in uri:
            t = 'm'
        else:
            continue

        # uri format: v2/<username>/<repo name>/[blobs/uploads | manifests]/<manifest or layer id>
        parts = uri.split('/')
        layer_or_manifest_id = parts[1] + '/' + parts[2] + '/' + parts[3] + '/' + str(size) # repo + layer id as layers unique identifier
        if t == 'm':
            size = 0
        requests.append({'timestamp': timestamp, 
                        'client': request['http.request.remoteaddr'], 
                        'method': request['http.request.method'], 
                        'type': t,
                         'size': size,
                         'id': layer_or_manifest_id 
        })
    return requests


def init(data, portion):

    requests = extract(data)

    print 'running simulation'

    size_layers = {
        5: 2783961371429,
        10: 3733953345324,
        25: 4932029114665,
        50: 5963318483606,
        75: 6754128982235,
        100: 7719397028187
                  }

    print 'running simulation'
    # cache sizes

    size1 = int(size_layers[portion] * 0.05)
    size2 = int(size_layers[portion] * 0.1)
    size3 = int(size_layers[portion] * 0.15)
    # size4 = int(size_layers[portion] * 0.2)
    # size5 = int(size_layers[portion] * 0.3)

    siftsize1 = siftcache(size1, 0) 
    siftsize2 = siftcache(size2, 0) 
    siftsize3 = siftcache(size3, 0) 
    # siftsize1 = siftcache(size1, 1) 
    # siftsize1 = siftcache(size1, 1) 
    # prefetchhour10 = prefetch_cache(rtimeout=3600, mtimeout=600)
    # prefetchhourhour = prefetch_cache(rtimeout=3600, mtimeout=3600)
    # prefetchhourhalf = prefetch_cache(rtimeout=3600, mtimeout=43200)
    # prefetchhourday = prefetch_cache(rtimeout=3600, mtimeout=86400)
    # prefetchhalf10 = prefetch_cache(rtimeout=43200, mtimeout=600)
    # prefetchhalfhour = prefetch_cache(rtimeout=43200, mtimeout=3600)
    # prefetchhalfhalf = prefetch_cache(rtimeout=43200, mtimeout=43200)
    # prefetchhalfday = prefetch_cache(rtimeout=43200, mtimeout=86400)
    # prefetchday10 = prefetch_cache(rtimeout=86400, mtimeout=600)
    # prefetchdayhour = prefetch_cache(rtimeout=86400, mtimeout=3600)
    # prefetchdayhalf = prefetch_cache(rtimeout=86400, mtimeout=43200)
    # prefetchdayday = prefetch_cache(rtimeout=86400, mtimeout=86400)
    i = 0
    j = 0
    l = len(requests)
    count = 0
    print "start putting data in cache"
    for request in requests:
        if 1.*i / l > 0.1:
            count += 10
            i = 0
            print str(count) + '% done'
        i += 1
        j += 1
        siftsize1.put(request)
        siftsize2.put(request)
        siftsize3.put(request)
        # prefetchhour10.put(request)
        # prefetchhourhour.put(request)
        # prefetchhourhalf.put(request)
        # prefetchhourday.put(request)
        # prefetchhalf10.put(request)
        # prefetchhalfhour.put(request)
        # prefetchhalfhalf.put(request)
        # prefetchhalfday.put(request)
        # prefetchday10.put(request)
        # prefetchdayhour.put(request)
        # prefetchdayhalf.put(request)
        # prefetchdayday.put(request)
    # prefetchhour10.flush()
    # prefetchhourhour.flush()
    # prefetchhourhalf.flush()
    # prefetchhourday.flush()
    # prefetchhalf10.flush()
    # prefetchhalfhour.flush()
    # prefetchhalfhalf.flush()
    # prefetchhalfday.flush()
    # prefetchday10.flush()
    # prefetchdayhour.flush()
    # prefetchdayhalf.flush()
    # prefetchdayday.flush()
    

    data = [
        siftsize1.get_info(),
        siftsize2.get_info(),
        siftsize3.get_info(),
            # prefetchhourhour.get_info(),
            # prefetchhourhalf.get_info(),
            # prefetchhourday.get_info(),
            # prefetchhalf10.get_info(),
            # prefetchhalfhour.get_info(),
            # prefetchhalfhalf.get_info(),
            # prefetchhalfday.get_info(),
            # prefetchday10.get_info(),
            # prefetchdayhour.get_info(),
            # prefetchdayhalf.get_info(),
            # prefetchdayday.get_info()
    ]
    
    print data
    f2 = open("siftcache_trace_detail.txt", 'a')
    msg = str(portion)+"% trace\n"
    f2.write(msg)
    for n in data:
        f2.write(str(n) + '\n') 
    f2.close()
