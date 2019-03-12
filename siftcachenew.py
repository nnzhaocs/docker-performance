import datetime
from collections import defaultdict
from collections import defaultdict
from lru import LRU
import pdb

import json



rlmaplocation = "/home/nannan/dockerimages/docker-traces/data_centers/usr2repo2layer_map.json"

class siftcache:

    def __init__(self, threshold):
        """layers get evicted from layer buffer and prefetched layers list when their timestamp
        exceeds the duration (in seconds) from the current time"""
        
        rlmapfp = open(rlmaplocation)
        self.RLmap = json.load(rlmapfp)
        rlmapfp.close()

        self.URLmap = defaultdict(lambda: defaultdict(set)) # map of {client: {repo1 : [layer1, layer2, layer3...]
                                                            #                  repo2 : [..]
                                                            #                 }
                                                            # updated during the request process
        self.layer_buffer = {}
        self.prefetched_layers_buffer = {}
        self.total_evictions = 0
        self.threshold = threshold

        
        # hits and misses
        ## total
        self.hit = 0
        self.miss = 0
        ## prefetch layers
        self.prefetch_layers_hit = 0
        self.prefetch_layers_miss = 0
        ##  layer buffer
        self.layer_buffer_hit = 0
        self.layer_buffer_miss = 0



    # def cacheeviction(self):
    #     self.usrs_in_cache_over_time.append(len(self.usr_lru.items()))
    #     while self.free_buffer < self.size_threshold:
    #         last_usr = self.usr_lru.peek_last_item()[0]
    #         reverse_layerlru_list = self.layer_lru.items()[::-1]
    #         for layerid, i_i in reverse_layerlru_list:
    #             if 'manifest' not in layerid and len(list(self.layer_usr_map[layerid])) == 1 and list(self.layer_usr_map[layerid])[0] == last_usr:
    #                 del self.layer_lru[layerid]
    #                 del self.layer_usr_map[layerid]
    #                 self.free_buffer += self.layer_size_map[layerid]
    #                 del self.layer_size_map[layerid]
    #             else:
    #                 self.layer_usr_map[layerid].discard(last_usr)
    #             self.total_evictions += 1
    #         del self.usr_lru[last_usr]
    #         self.eviction_times.append(self.free_buffer)
           
           

    # def pushintocache(self, request):
    #     # print "space left in user cache: "+str(9997-len(self.usr_lru.items()))
    #     if self.layer_lru.has_key(request['id']):
    #         self.layer_lru[request['id']] = self.layer_lru[request['id']] + 1
    #         if self.usr_lru.has_key(request['client']):
    #             self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
    #         else:
    #             self.usr_lru[request['client']] = 1
    #         self.layer_usr_map[request['id']].add(request['client'])
    #     else:
    #         self.layer_lru[request['id']] = 1
    #         self.layer_size_map[request['id']] = request['size']
    #         self.layer_usr_map[request['id']].add(request['client'])
    #         if self.usr_lru.has_key(request['client']):
    #             self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
    #         else:
    #             self.usr_lru[request['client']] = 1
    #         self.free_buffer -= self.layer_size_map[request['id']]
    #     if self.free_buffer < self.size_threshold:
    #         self.cacheeviction() 
    # def pullfromcache(self, request):
    #     # print "space left in user cache: "+str(9997-len(self.usr_lru.items())) #     if self.layer_lru.has_key(request['id']): #         self.layer_lru[request['id']] = self.layer_lru[request['id']] + 1
    #         if self.usr_lru.has_key(request['client']):
    #             self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1
    #         else:
    #             self.usr_lru[request['client']] = 1
    #         self.layer_usr_map[request['id']].add(request['client'])
    #         self.hit += 1
    #     else:
    #         self.miss += 1
    #         self.layer_lru[request['id']] = 1
    #         self.layer_size_map[request['id']] = request['size']
    #         self.layer_usr_map[request['id']].add(request['client'])
    #         if self.usr_lru.has_key(request['client']):
    #             self.usr_lru[request['client']] = self.usr_lru[request['client']] + 1la
    #         else:
    #             self.usr_lru[request['client']] = 1
    #         self.free_buffer -= self.layer_size_map[request['id']]
    #     if self.free_buffer < self.size_threshold:
    #         self.cacheeviction()
        
        

    def prefetch_layers(self, request):
        client = request['client']
        repo = request['repo']
        client_layers = list(self.URLmap[client][repo])
        try:
            repo_layers = self.RLmap[repo]
        except KeyError:
            self.RLmap[repo] = []
            repo_layers = self.RLmap[repo]

        prefetchable = set(repo_layers).difference(set(client_layers))
        to_prefetch = list(set(prefetchable).difference(set(self.prefetched_layers_buffer.keys())))
        for layer in to_prefetch:
            self.prefetched_layers_buffer[layer] = request['timestamp']

    def buffer_layer(self, request):
        layer = request['putid']
        self.layer_buffer[layer] = request['timestamp']
    
    def update_URLmap(self, request):
        client = request['client']
        repo = request['repo']
        if request['method'] == 'PUT':
            layer = request['putid']
        else:
            layer = request['getid']
        self.URLmap[client][repo].add(layer)

    def update_RLmap(self, request):
        client = request['client']
        repo = request['repo']
        if request['method'] == 'PUT':
            layer = request['putid']
        else:
            layer = request['getid']
        try:
            self.RLmap[repo].append(layer)
        except KeyError:
            self.RLmap[repo] = [layer]


    def evictions(self, now_time):
        for layer in self.layer_buffer.keys():
            layer_time = self.layer_buffer[layer]
            timediff = now_time - layer_time
            if timediff.seconds > self.threshold:
                del self.layer_buffer[layer]
                self.total_evictions += 1

        for layer in self.prefetched_layers_buffer.keys():
            layer_time = self.prefetched_layers_buffer[layer]
            timediff = now_time - layer_time
            if timediff.seconds > self.threshold:
                del self.prefetched_layers_buffer[layer]
                self.total_evictions += 1
    
    def put(self, request):
        if request['method'] == 'GET' and request['type'] == 'm': 
            self.prefetch_layers(request)

        elif request['method'] == 'PUT' and request['type'] == 'l':
            self.update_URLmap(request)
            self.update_RLmap(request)
            self.buffer_layer(request)

        elif request['method'] == 'GET' and request['type'] == 'l':
            if request['putid'] in self.layer_buffer:
                self.layer_buffer_hit += 1
                self.hit += 1
                self.update_URLmap(request)
                self.layer_buffer[request['putid']] = request['timestamp']

            elif request['getid'] in self.prefetched_layers_buffer: 
                self.prefetch_layers_hit += 1
                self.hit += 1
                self.update_URLmap(request)
                self.prefetched_layers_buffer[request['getid']] = request['timestamp']
                
            elif request['putid'] in self.prefetched_layers_buffer:
                self.prefetch_layers_hit += 1
                self.hit += 1
                self.update_URLmap(request)
                self.prefetched_layers_buffer[request['putid']] = request['timestamp']

            else:
                self.prefetch_layers_miss += 1
                self.layer_buffer_miss += 1
                self.miss += 1
                self.update_URLmap(request)
                self.prefetch_layers(request)


        self.evictions(request['timestamp'])


        

    def get_info(self):
        data = {
            'hits': self.hit,
            'misses': self.miss,
            'hit ratio': (self.hit*1.0)/(self.hit +self.miss),
            'layer buffer hits': self.layer_buffer_hit,
            'layer buffer misses': self.layer_buffer_miss,
            'layer buffer hit ratio': (self.layer_buffer_hit*1.0)/(self.layer_buffer_hit +self.layer_buffer_miss),
            'prefetch layer hits': self.prefetch_layers_hit,
            'prefetch layer misses': self.prefetch_layers_miss,
            'prefetch layer hit ratio': (self.prefetch_layers_hit*1.0)/(self.prefetch_layers_hit +self.prefetch_layers_miss),
            'threshold': self.threshold,
            'evictions over lifetime': self.total_evictions,
            }
        return data

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
        layer_or_manifest_id = parts[1] + '/' + parts[2] + '/' + str(size) # repo + layer id as layers unique identifier
        if t == 'm':
            size = 0
        requests.append({'timestamp': timestamp, 
                        'client': request['http.request.remoteaddr'], 
                        'method': request['http.request.method'], 
                         'repo': parts[1]+'/'+parts[2],
                        'type': t,
                         'size': size,
                         'getid': parts[-1],
                         'putid': layer_or_manifest_id,
        })
    return requests


def init(data, portion):

    requests = extract(data)

    print 'running simulation'


    # size1 = int(size_layers[portion] * 0.05)
    # size2 = int(size_layers[portion] * 0.1)
    # size3 = int(size_layers[portion] * 0.15)
    # size4 = int(size_layers[portion] * 0.2)
    # size5 = int(size_layers[portion] * 0.3)

    siftsize1 = siftcache(600) # 10 minutes
    
    # siftsize2 = siftcache( <threshold>) 
    # siftsize3 = siftcache( <threshold>) 
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
    pdb.set_trace()
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
        if j == 600:
            pdb.set_trace()
        siftsize1.put(request)
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
