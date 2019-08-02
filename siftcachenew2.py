from argparse import ArgumentParser
import datetime
from collections import defaultdict
from collections import defaultdict
from lru import LRU
import pdb
import yaml
import json

from organize_requests import *

rlmaplocation = "/home/nannan/dockerimages/docker-traces/data_centers/usr2repo2layer_map_with_size.json"
urlmaplocation = "/home/nannan/dockerimages/docker-traces/downloaded-traces/data_centers/dev-mon01_total_trace.json-repo2layersdic.json"

def mean(items):
    return sum(items)*1.0/len(items)

class siftcache:

    def __init__(self, threshold):
        """layers get evicted from layer buffer and prefetched layers list when their timestamp
        exceeds the duration (in seconds) from the current time"""
        
        rlmapfp = open(rlmaplocation)
        self.RLmap = json.load(rlmapfp)
        rlmapfp.close()
        for repo in self.RLmap.keys():
            layerdict = {}
            for layer,size in self.RLmap[repo]:
                layerdict[layer] = size
            self.RLmap[repo] = layerdict

        urlmapfp = open(urlmaplocation)
        self.URLmap = json.load(urlmapfp)#defaultdict(lambda: defaultdict(set)) # map of {client: {repo1 : [layer1, layer2, layer3...]
        urlmapfp.close()
                                                            #                  repo2 : [...]
                                                            #                 }
                                                            # updated during the request process
        self.layer_buffer = {}
        self.layer_buffer_space_usage = []
        self.layer_buffer_space = 0
        self.prefetched_layers_buffer = {}
        self.prefetched_layers_buffer_space_usage = []
        self.prefetched_layers_buffer_space = 0
        self.total_evictions = 0
        self.threshold = threshold
       
        # hits and misses
        ## total
        self.hit = 0
        self.miss = 0
        ## prefetch layers
        self.prefetch_layers_hit = 0
#         self.prefetch_layers_miss = 0
        ##  layer buffer
        self.layer_buffer_hit = 0
#         self.layer_buffer_miss = 0
        
        ###nannan: 
#         self.pecentage
        self.recent_prefetched_slicelayers = 0
        self.recent_buffered_putlayers = 0
        self.sediments = 0



    def prefetch_layers(self, request):
        print 'entered prefetch layers'
        client = request['client']
        repo = request['repo']

        print 'RLMAP ' + str(self.RLmap[repo])
        print 'URLMAP' + str(self.URLmap[client])
        print ' req ' + str(request)
        client_layers = list(self.URLmap[client][repo])
        print 'layers ' + client_layers
        try:
            repo_layers = self.RLmap[repo].keys()
        except KeyError:
            print'key error'
            self.RLmap[repo] = {}
            repo_layers = self.RLmap[repo].keys()

        prefetchable = set(repo_layers).difference(set(client_layers))
        print 'prefetchable: ' + str(prefetchable)
        print 'self buffer: ' + str(self.prefetched_layers_buffer)
        to_prefetch = list(set(prefetchable).difference(set(self.prefetched_layers_buffer.keys())))
        to_prefetch_excluding_putbuffer = list(set(to_prefetch).difference(self.buffer_layer.keys()))
        #nannan
        self.recent_prefetched_slicelayers += len(to_prefetch_excluding_putbuffer)
#         self.sediments += len(set(self.prefetched_layers_buffer.keys()))
        
        for layer in to_prefetch:
            self.prefetched_layers_buffer[layer] = {'timestamp': request['timestamp'],
                                                    'size': self.RLmap[repo][layer],
                                                    }

            
            

    def buffer_layer(self, request):
        layer = request['id']
        self.recent_buffered_putlayers += 1
        self.layer_buffer[layer] = {'timestamp': request['timestamp'],
                                    'size': request['size'],
        }

    
    def update_URLmap(self, request):
        client = request['client']
        repo = request['repo']
        if request['method'] == 'PUT':
            layer = request['id']
#         else:
#             layer = request['getid']
        self.URLmap[client][repo].add(layer)

    def update_RLmap(self, request):
        client = request['client']
        repo = request['repo']
        if request['method'] == 'PUT':
            layer = request['id']
#         else:
#             layer = request['getid']
        try:
            self.RLmap[repo][layer] = request['size']
        except KeyError:
            self.RLmap[repo] = {layer: request['size']}


    def evictions(self, now_time):
        self.layer_buffer_space_usage.append(sum([self.layer_buffer[layer]['size'] for layer in self.layer_buffer]))
        self.sediments += len(self.layer_buffer.keys()) - self.recent_buffered_putlayers
        
        self.prefetched_layers_buffer_space_usage.append(sum([self.prefetched_layers_buffer[layer]['size'] for layer in self.prefetched_layers_buffer]))
        self.sediments += len(self.prefetched_layers_buffer.keys()) - self.recent_prefetched_slicelayers
        
        for layer in self.layer_buffer.keys():
            layer_time = self.layer_buffer[layer]['timestamp']
            timediff = now_time - layer_time
            if timediff.seconds > self.threshold:
                self.layer_buffer_space -= self.layer_buffer[layer]['size']
                del self.layer_buffer[layer]
                self.total_evictions += 1

        for layer in self.prefetched_layers_buffer.keys():
            layer_time = self.prefetched_layers_buffer[layer]['timestamp']
            timediff = now_time - layer_time
            if timediff.seconds > self.threshold:
                self.prefetched_layers_buffer_space -= self.prefetched_layers_buffer[layer]['size']
                del self.prefetched_layers_buffer[layer]
                self.total_evictions += 1
    
    def put(self, request):
        print 'entered put'
        if request['method'] == 'GET' and request['type'] == 'm': 
            self.prefetch_layers(request)

        elif request['method'] == 'PUT' and request['type'] == 'l':
            self.update_URLmap(request)
            self.update_RLmap(request)
            self.buffer_layer(request)

        elif request['method'] == 'GET' and request['type'] == 'l':
            if request['id'] in self.layer_buffer:
                self.layer_buffer_hit += 1
#                 self.prefetch_layers_miss += 1
                self.hit += 1
                self.update_URLmap(request)
                self.layer_buffer[request['id']]['timestamp'] = request['timestamp']

            elif request['id'] in self.prefetched_layers_buffer: 
                self.prefetch_layers_hit += 1
#                 self.layer_buffer_miss += 1
                self.hit += 1
                self.update_URLmap(request)
                self.prefetched_layers_buffer[request['id']]['timestamp'] = request['timestamp']
                
#             elif request['putid'] in self.prefetched_layers_buffer: # what is this? manifests?
#                 self.prefetch_layers_hit += 1
#                 self.hit += 1
#                 self.layer_buffer_miss += 1
#                 self.update_URLmap(request)
#                 self.prefetched_layers_buffer[request['putid']]['timestamp'] = request['timestamp']

            else:
#                 self.prefetch_layers_miss += 1
#                 self.layer_buffer_miss += 1
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
#             'layer buffer misses': self.layer_buffer_miss,
#             'layer buffer hit ratio': (self.layer_buffer_hit*1.0)/(self.layer_buffer_hit +self.layer_buffer_miss),
            'layer buffer max usage': max(self.layer_buffer_space_usage),
            'layer buffer average usage': mean(self.layer_buffer_space_usage),
            'prefetch layer hits': self.prefetch_layers_hit,
#             'prefetch layer misses': self.prefetch_layers_miss,
#             'prefetch layer hit ratio': (self.prefetch_layers_hit*1.0)/(self.prefetch_layers_hit +self.prefetch_layers_miss),
            'prefetch layer buffer max usage': max(self.prefetched_layers_buffer_space_usage),
            'prefetch layer buffer average usage': mean(self.prefetched_layers_buffer_space_usage),
            'threshold': self.threshold,
            'evictions over lifetime': self.total_evictions,
            'recent prefetched slice layers': self.recent_prefetched_slicelayers,
            'recent buffered put layers': self.recent_buffered_putlayers,
            'sediments': self.sediments,
            'sediment hits': ((self.hit - self.recent_buffered_putlayers)*1.0)
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
        #nannan
#         layer_or_manifest_id = parts[1] + '/' + parts[2] + '/' + str(size) # repo + layer id as layers unique identifier
        layer_or_manifest_id = uri.rsplit('/', 1)[1]
        if t == 'm':
            size = 0
        requests.append({'timestamp': timestamp, 
                        'client': request['http.request.remoteaddr'], 
                        'method': request['http.request.method'], 
                         'repo': parts[1]+'/'+parts[2],
                        'type': t,
                         'size': size,
                         'id': layer_or_manifest_id,
#                          'putid': layer_or_manifest_id,
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

    siftsize1 = siftcache(60) # 1 minutes
    siftsize2 = siftcache(300) # 5 minutes
    siftsize3 = siftcache(600) # 10 minutes
    siftsize4 = siftcache(900) # 15 minutes
    siftsize5 = siftcache(1200) # 20 minutes
    
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
        print "req: type" + str(type(request))
        print request
        siftsize1.put(request)
        siftsize2.put(request)
        siftsize3.put(request)
        siftsize4.put(request)
        siftsize5.put(request)
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
        siftsize4.get_info(),
        siftsize5.get_info(),
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
    print 'trying to write to siftcache_trace_detail.txt'
    f2 = open("siftcache_trace_detail.txt", 'a')
    msg = str(portion)+"% trace\n"
    f2.write(msg)
    for n in data:
        f2.write(str(n) + '\n') 
    f2.close()
####################################################
#generate and read in blob json files
def main():
    data = []
    #get config file
    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    args = parser.parse_args()
    
    print 'trying to read config file...'
    config = file(args.input, 'r')
    try:
        inputs = yaml.load(config)
    except Exception as inst:
        print 'error reading config file'
	print inst
        exit(-1)
    if 'trace' not in inputs:
        print 'trace field required in config file'
        exit(1)
    print 'config reading successful'

    ##run match
    print 'perparing for match...'
    #realblobs
    realblob_locations = []
    print 'realblobs successful'
    if 'realblobs' in inputs['client_info']:
        realblob_locations = inputs['client_info']['realblobs']
    else:
        exit(-1)
    #trace_files
    trace_files = []
    layeridmap = []

    if 'location' in inputs['trace']:
        location = inputs['trace']['location']
        if '/' != location[-1]:
            location += '/'
        for fname in inputs['trace']['traces']:
            trace_files.append(location + fname)
            layeridmap.append(location + fname)
    else:
        trace_files.extend(inputs['trace']['traces'])
        layeridmap.extend(inputs['trace']['traces'])

    print 'Input traces'
    for f in trace_files:
        print f

    getonly = False
    #if inputs['simulate']['getonly'] == True:
    #    getonly = True
    #    print("getonly or not?", getonly)

    print 'trace files successful'
    #limit
    limit_type = None
    limit = 0
    if 'limit' in inputs['trace']:
        limit_type = inputs['trace']['limit']['type']
        if limit_type in ['seconds', 'requests']:
            limit = inputs['trace']['limit']['amount']
        else:
            print 'Invalid trace limit_type: limit_type must be either seconds or requests'
            exit(1)
    print 'limit successful'
    print 'now running match'
    match(realblob_locations, trace_files, limit, getonly, layeridmap)
    print 'match successful'

    print 'reading in requests...'
    data = []
    for filename in trace_files:
        with open(filename+'-realblob.json', 'r') as f:
            data.extend(json.load(f))
    print 'requests read in successfully'
    print 'data length: ' + str(len(data))

    print 'now running init...'
    init(data, 10)
    print 'successful, results written to file'

if __name__ == "__main__":
    main()
