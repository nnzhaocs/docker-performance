import datetime
import pdb
from lru import LRU

import rejson, redis, json
from Carbon.Aliases import false

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

class redis_table:
    def __init__(self, redis_host, redis_port):
        self.rjpool_dbNoUsrecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoUsrecipe)
        self.rj_dbNoUsrecipe = redis.Redis(connection_pool=rjpool_dbNoUsrecipe)
        
        self.rjpool_dbNoReporecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoReporecipe)
        self.rj_dbNoReporecipe = redis.Redis(connection_pool=rjpool_dbNoReporecipe)
        
        self.rjpool_dbNoMefrecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoMefrecipe)
        self.rj_dbNoMefrecipe = redis.Redis(connection_pool=rjpool_dbNoMefrecipe)
        
        self.rjpool_dbNoLyrecipe = redis.ConnectionPool(host = redis_host, port = redis_port, db = dbNoLyrecipe)
        self.rj_dbNoLyrecipe = redis.Redis(connection_pool=rjpool_dbNoLyrecipe)
        
    def update_clients(self, repo, client, timestamp): 
        if not rj_dbNoUsrecipe.exists(client):
            reply = [(repo, timestamp, 1)]
        else:
            reply = json.loads(rj_dbNoUsrecipe.execute_command('JSON.GET', client))
            print "get reply from client: " 
            print reply
            find = False
            for tub in reply:
                if repo == tub[0]:
                    tub[1] = timestamp
                    tub[2] += 1
                    find = True
            if find == False:
                reply.append((repo, timestamp, 1))
            rj_dbNoUsrecipe.execute_command('JSON.SET', client, '.', json.dumps(reply))
        
    def update_repos(self, repo, layer_id, size, timestamp,): # with layers
        if not rj_dbNoReporecipe.exists(repo):
            reply = [(layer_id, timestamp, cnt, size)]
        else:
            reply = json.loads(rj_dbNoReporecipe.execute_command('JSON.GET', repo))
            print "get reply from client: " 
            print reply
            find = False
            for tub in reply:
                if layer_id == tub[0]:
                    tub[1] = timestamp
                    tub[2] += 1
                    find = True
            if find == False:
                reply.append((layer_id, timestamp, 1, size))
            rj_dbNoReporecipe.execute_command('JSON.SET', repo, '.', json.dumps(reply))
        
    def update_manifests(self, repo, manifest_id, timestamp):
        if not rj_dbNoMefrecipe.exists(repo):
            reply = [(manifest_id, timestamp, cnt)]
        else:
            reply = json.loads(rj_dbNoMefrecipe.execute_command('JSON.GET', repo))
            print "get reply from client: " 
            print reply
            find = False
            for tub in reply:
                if manifest_id == tub[0]:
                    tub[1] = timestamp
                    tub[2] += 1
            if find == False:
                reply.append((manifest_id, timestamp, 1))
            rj_dbNoMefrecipe.execute_command('JSON.SET', repo, '.', json.dumps(reply))     
        
    def update_layers(self, client, repo, layer_id):
        if not rj_dbNoLyrecipe.exists(layer_id):
            reply = [(client, repo)]
        else:
            reply = json.loads(rj_dbNoLyrecipe.execute_command('JSON.GET', repo))
            print "get reply from client: " 
            print reply
            find = False
            for tub in reply:
                if client == tub[0] and repo == tub[1]:
                    find = True
            if find = False:
                reply.append((client, repo))
            rj_dbNoLyrecipe.execute_command('JSON.SET', repo, '.', json.dumps(reply))          
        

class siftcache:

    def __init__(self, size, rtimeout=600, mtimeout=600):
#         self.repos = {}
#         self.manifest = {}
#         self.rtimeout = rtimeout
#         self.mtimeout = mtimeout
        self.hit = 0
        self.miss = 0
#         self.size = 0
#         self.usr_lru = []
#         self.size_list = []
#         self.goodprefetch = 0
#         self.badprefetch = 0
        
        self.putcount = 0
        self.putmanifest_cnt = 0
        self.putlayer_cnt = 0
        
        self.getlayercount = 0
        self.getmanifestcount = 0
        
        self.size = size # actual size of the cache
        
        self.usr_lru = LRU(9997)
        self.repo_lru = LRU(40264)
        self.layer_lru = LRU(829202)

        self.hits = 0.0
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
        
    def update_usermaplru(self, usr, repo, layer_id, manifest_id):
        if layer_id:
            
            

    def flush(self):
        for repo in self.manifest:
            for layer in self.manifest[repo]:
                count = layer[1]
                self.size -= layer[2]
                self.size_list.append(self.size)
                if count > 0:
                    self.goodprefetch += 1
                else:
                    self.badprefetch += 1
        self.manifest = {}

    def update_manifests(self, repo, client, timestamp):
        # you can't pull a manifest if the repo doesn't exist, hence why we don't have the else
        # condition
        if self.repo_lru.has_key(repo): 
            for layer in self.repos[repo]:
                if client not in layer[1]:
                    # layer: [timestamp, [client1, client2, ...], size]
                    layer[1].append(client)
                    if repo not in self.manifest:
                        self.manifest[repo] = [[timestamp, 0, layer[2], layer[3]]]
                        self.size += layer[2]
                        self.size_list.append(self.size)
                    else:
                        present = False
                        for fetchedlayer in self.manifest[repo]:
                            if fetchedlayer[3] == layer[3]:
                                fetchedlayer[0] = timestamp
                                present = True
                                break
                        if present == False:
                            self.manifest[repo].append([timestamp, 0, layer[2], layer[3]])
                            self.size += layer[2]
                            self.size_list.append(self.size)



    def manifest_time_out(self, timestamp):
        remove = []
        for repo in self.manifest:
            i = 0
            while i < len(self.manifest[repo]):
                t = self.manifest[repo][i][0]
                count = self.manifest[repo][i][1]
                delta = timestamp - t
                if delta.seconds > self.mtimeout:
                    print("timeout for ", repo)
                    self.size -= self.manifest[repo][i][2]
                    self.size_list.append(self.size)
                    self.manifest[repo].pop(i)
                    if count > 0:
                        self.goodprefetch += 1
                    else:
                        self.badprefetch += 1
                else:
                    i += 1
            if len(self.manifest[repo]) == 0:
                remove.append(repo)
        for repo in remove:
            self.manifest.pop(repo, None)

    # the self.repos represent the backend of the registry. It should not timeout.
    # at least, that's my impression of it.
    def repo_time_out(self, timestamp):
        remove = []
        for repo in self.repos:
            i = 0
            while i < len(self.repos[repo]):
                t = self.repos[repo][i][0]
                delta = timestamp - t
                if abs(delta) > self.rtimeout:
                    self.repos[repo].pop(i)
                else:
                    break
            if len(self.repos[repo]) == 0:
                remove.append(repo)
        for repo in remove:
            self.repos.pop(repo, None)

    def update_repos(self, repo, client, size, timestamp, layer_id):
        if repo in self.repos:
            self.repos[repo].append([timestamp, [client], size, layer_id])
        else:
            self.repos[repo] = [[timestamp, [client], size, layer_id]]

    def update_layers(self, repo, size, timestamp, layer_id):
        if repo in self.manifest:
            for layer in self.manifest[repo]:

                if layer[3] == layer_id:
                    self.hit += 1
                    layer[1] += 1
        else:
            self.miss += 1
        
    def put(self, request):
        repo = request['repo']
        client = request['client']
        timestamp = request['timestamp']
        size = request['size']
        layer_or_manifest_id = request['id']
        
        # here is when eviction starts ======>
        # select some repo to evict.
        self.manifest_time_out(timestamp)
        self.repo_time_out(timestamp) # this shouldn't run
        
        # here 
        
        if request['method'] == 'PUT' and request['type'] == 'm':
            return
        elif request['method'] == 'PUT': 
            self.putcount += 1
            self.update_repos(repo, client, size, timestamp, layer_or_manifest_id)
        elif request['type'] == 'm':
            self.getmanifestcount += 1
            self.update_manifests(repo, client, timestamp)
        else:
            self.getlayercount += 1
            self.update_layers(repo, size, timestamp, layer_or_manifest_id)

    def get_info(self):
        data = {
            'hits': self.hit,
            'misses': self.miss,
            'good prefetch': self.goodprefetch,
            'bad prefetch': self.badprefetch,
            'max size': max(self.size_list)}
        return data

    def get_size_list(self):
        return self.size_list

def extract(data):
  
    requests = []

    for request in data:
        method = request['http.request.method']

        uri = request['http.request.uri']
        timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if 'blobs' in uri:
            t = 'l'
        elif 'manifests' in uri:
            t = 'm'
        else:
            continue

        # uri format: v2/<username>/<repo name>/[blobs/uploads | manifests]/<manifest or layer id>
        layer_or_manifest_id = uri.rsplit('/', 1)[1]
        parts = uri.split('/')
        repo = parts[1] + '/' + parts[2]
        requests.append({'timestamp': timestamp, 
                        'repo': repo, 
                        'client': request['http.request.remoteaddr'], 
                        'method': request['http.request.method'], 
                        'type': t,
                         'size': request['http.response.written'],
                         'id': layer_or_manifest_id 
        })
    return requests


def init(data):

    requests = extract(data)

    print 'running simulation'

    prefetch1010 = prefetch_cache(rtimeout=600, mtimeout=600)
    prefetch10hour = prefetch_cache(rtimeout=600, mtimeout=3600)
    prefetch10half = prefetch_cache(rtimeout=600, mtimeout=43200)
    prefetch10day = prefetch_cache(rtimeout=600, mtimeout=86400)
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
        if j == 70000 or j == 500000 or j == 1000000:
            pdb.set_trace()
        prefetch1010.put(request)
        prefetch10hour.put(request)
        prefetch10half.put(request)
        prefetch10day.put(request)
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
    prefetch1010.flush()
    prefetch10hour.flush()
    prefetch10half.flush()
    prefetch10day.flush()
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
    

    data = [prefetch1010.get_info(),
            prefetch10hour.get_info(),
            prefetch10half.get_info(),
            prefetch10day.get_info(),
            # prefetchhour10.get_info(),
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
    
    outfile = "prefetch_trace.txt"
    f1 = open(outfile, 'a')
    f2 = open("prefetch_trace_detail.txt", 'a')
    for n in data:
        f2.write(str(n) + '\n') 
        size = n['max size']
        ratio = 1.*n['hits'] / (n['good prefetch'] + n['bad prefetch'])
        f1.write(str(ratio) + ',' + str(size) + '\n')
    f1.close()
    f2.close()
