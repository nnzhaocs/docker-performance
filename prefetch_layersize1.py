"""
same as anwar's prefetch, but now with limiting the cache size to a percentage of
total number of layers (as calculated by counting the unique layers in all the GET
requests

If we need to prefetch a repo and place it in the cache, we must first check if
adding that repo will exceed cache capacity. If it does, we will evict a repo
at random from the cache and then prefetch the current repo
"""

import datetime
import pdb
import random

class prefetch_cache:

    def __init__(self, rtimeout=600, mtimeout=600, cache_size=10000):
        self.repos = {}
        self.manifest = {}
        self.rtimeout = rtimeout
        self.mtimeout = mtimeout
        self.hit = 0
        self.miss = 0
        self.size = 0
        self.capacity = cache_size
        self.size_list = []
        self.goodprefetch = 0
        self.badprefetch = 0
        self.putcount = 0
        self.getlayercount = 0
        self.getmanifestcount = 0

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
        # TODO: modify this func to evict random repo from the prefetch cache
        # when cache size limit reached
        if repo in self.repos:
            for layer in self.repos[repo]:
                if client not in layer[1]:
                    layer[1].append(client)
                    if repo not in self.manifest:
                        if (self.size + layer[2]) > self.capacity:
                            # evict random repo from cache if cache is expected to become overcapacity
                            while True:
                               evict_repo = random.choice(self.manifest.keys())
                               if evict_repo != repo:
                                   evict_repo_size = sum([layer[2] for layer in self.manifest[evict_repo]])
                                   self.size -= evict_repo_size
                                   self.manifest.pop(evict_repo)
                                   break
                               else:
                                   continue

                        self.manifest[repo] = [[timestamp, 0, layer[2]]]
                        self.size += layer[2]
                        self.size_list.append(self.size)
                    else:
                        present = False
                        for fetchedlayer in self.manifest[repo]:
                            if fetchedlayer[2] == layer[2]:
                                fetchedlayer[0] = timestamp
                                present = True
                                break
                        if present == False:
                            if (self.size + layer[2]) > self.capacity:
                                # evict random repo from cache if cache is expected to become overcapacity
                                while True:
                                    evict_repo = random.choice(self.manifest.keys())
                                    if evict_repo != repo:
                                        evict_repo_size = sum([layer[2] for layer in self.manifest[evict_repo]])
                                        self.size -= evict_repo_size
                                        self.manifest.pop(evict_repo)
                                        break
                                    else:
                                        continue
                            self.manifest[repo].append([timestamp, 0, layer[2]])
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

    def repo_time_out(self, timestamp):
        remove = []
        for repo in self.repos:
            i = 0
            while i < len(self.repos[repo]):
                t = self.repos[repo][i][0]
                delta = timestamp - t
                if delta.seconds > self.rtimeout:
                    self.repos[repo].pop(i)
                else:
                    break
            if len(self.repos[repo]) == 0:
                remove.append(repo)
        for repo in remove:
            self.repos.pop(repo, None)

    def update_repos(self, repo, client, size, timestamp):
        if repo in self.repos:
            self.repos[repo].append([timestamp, [client], size])
        else:
            self.repos[repo] = [[timestamp, [client], size]]

    def update_layers(self, repo, size, timestmap):
        if repo in self.manifest:
            for layer in self.manifest[repo]:
                if size - 1000 < layer[2] and size + 1000 > layer[2]:
                    self.hit += 1
                    layer[1] += 1
        else:
            self.miss += 1

    def put(self, request):
        repo = request['repo']
        client = request['client']
        timestamp = request['timestamp']
        size = request['size']
        self.manifest_time_out(timestamp)
        self.repo_time_out(timestamp)
        if request['method'] == 'PUT':
            self.putcount += 1
            self.update_repos(repo, client, size, timestamp)
        elif request['type'] == 'm':
            self.getmanifestcount += 1
            self.update_manifests(repo, client, timestamp)
        else:
            self.getlayercount += 1
            self.update_layers(repo, size, timestamp)

    def get_info(self):
        data = {
            'hits': self.hit,
            'misses': self.miss,
            'hit ratio': self.hit*1.0/(self.hit+self.miss),
            'good prefetch': self.goodprefetch,
            'bad prefetch': self.badprefetch,
            'max size': max(self.size_list),
            'cache capacity': self.capacity
        }
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

        parts = uri.split('/')
        repo = parts[1] + '/' + parts[2]
        requests.append({'timestamp': timestamp,
                        'repo': repo,
                        'client': request['http.request.remoteaddr'],
                        'method': request['http.request.method'],
                        'type': t,
                        'size':request['http.response.written']
                        })
    return requests


def init(data, portion=100):

    requests = extract(data)

    # total size of the layers based on unique get requests, in each portion of the trace
    size_layers = {10:77456600001,
                   25: 158664779202,
                   50: 326091306553,
                   75: 400991300935,
                  100: 481877787818,
                  }

    print 'running simulation'
    # cache sizes

    size1 = int(size_layers[portion] * 0.05)
    size2 = int(size_layers[portion] * 0.1)
    size3 = int(size_layers[portion] * 0.15)
    size4 = int(size_layers[portion] * 0.2)
    size5 = int(size_layers[portion] * 0.3)

    # prefetch1010 = prefetch_cache(rtimeout=600, mtimeout=600, cache_size = )
    # prefetch10hour = prefetch_cache(rtimeout=600, mtimeout=3600)
    # prefetch10half = prefetch_cache(rtimeout=600, mtimeout=43200)
    prefetch10day_cache5p = prefetch_cache(rtimeout=600, mtimeout=86400, cache_size = size1)
    prefetch10day_cache10p = prefetch_cache(rtimeout=600, mtimeout=86400, cache_size = size2)
    prefetch10day_cache15p = prefetch_cache(rtimeout=600, mtimeout=86400, cache_size = size3)
    prefetch10day_cache20p = prefetch_cache(rtimeout=600, mtimeout=86400, cache_size = size4)
    prefetch10day_cache30p = prefetch_cache(rtimeout=600, mtimeout=86400, cache_size = size5)
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
        # if j == 70000 or j == 500000 or j == 1000000:
        #     pdb.set_trace()
        # prefetch1010.put(request)
        # prefetch10hour.put(request)
        # prefetch10half.put(request)
        prefetch10day_cache5p.put(request)
        prefetch10day_cache10p.put(request)
        prefetch10day_cache15p.put(request)
        prefetch10day_cache20p.put(request)
        prefetch10day_cache30p.put(request)
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
    # prefetch1010.flush()
    # prefetch10hour.flush()
    # prefetch10half.flush()
    prefetch10day_cache5p.flush()
    prefetch10day_cache10p.flush()
    prefetch10day_cache15p.flush()
    prefetch10day_cache20p.flush()
    prefetch10day_cache30p.flush()
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
        # prefetch1010.get_info(),
        # prefetch10hour.get_info(),
        # prefetch10half.get_info(),
        prefetch10day_cache5p.get_info(),
        prefetch10day_cache10p.get_info(),
        prefetch10day_cache15p.get_info(),
        prefetch10day_cache20p.get_info(),
        prefetch10day_cache30p.get_info(),
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

    outfile = "prefetch_trace_cachesizeset.txt"
    f1 = open(outfile, 'a')
    f2 = open("prefetch_trace_detail_cachesizeset_fra02.txt", 'a')
    for n in data:
        f2.write(str(n) + '\n')
        size = n['max size']
        ratio = 1.*n['hits'] / (n['good prefetch'] + n['bad prefetch'])
        f1.write(str(ratio) + ',' + str(size) + '\n')
    f1.close()
    f2.close()
