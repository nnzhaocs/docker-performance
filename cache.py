import time
import datetime
import yaml
import json
import requests
from argparse import ArgumentParser


class complex_cache:
    def __init__(self, size=1., restrict=100, fssize=10):
        self.lmu = []
        self.mem = {}
        self.capacity = int(size * (2**30))
        self.size = 0
        self.hits = 0
        self.misses = 0
        self.restrict = restrict*(2**20)
        self.firstmemhits = 0
        self.firstfsmemhits = 0
        self.firstfshits = 0
        if self.restrict > self.capacity:
            self.restrict = self.capacity
        self.evictions = 0
        self.first = True
        self.firstMiss = 0
        self.fslmu = []
        self.fs = {}
        self.fscap = self.capacity*fssize
        self.fssize = 0
        self.fsmiss = 0
        self.fsfirstMiss = 0
        self.fsfirst = True
        self.fshits = 0
        self.fsevicts = 0

    def fsCheck(self, request):
        if request[-1] in self.fs:
            self.fssize -= self.fs[request[-1]][0]
            self.fs.pop(request[-1], None)
            self.fshits += 1
            if self.fsfirst == True:
                self.firstfshits += 1
        else:
            self.fsmiss += 1
            if self.fsfirst == True:
                self.fsfirstMiss += 1

    def fsPlace(self, layer, layerSize, ejected=False):
        if layer in self.fs:
            self.fslmu.append(layer)
            self.fshits += 1
            self.fs[layer][1] += 1
            if self.fsfirst == True:
                self.firstfshits += 1
        else:
            if ejected is False:
                self.fsmiss += 1
                if self.fsfirst == True:
                    self.fsfirstMiss += 1

            if layerSize + self.fssize <= self.fscap:
                self.fs[layer] = [layerSize, 1]
                self.fssize += layerSize
                self.fslmu.append(layer)
            else:
                if self.fscap < layerSize:
                    return
                self.fsfirst = False
                while layerSize + self.fssize > self.fscap:
                    eject = self.fslmu.pop(0)
                    if eject not in self.fs:
                        continue
                    self.fs[eject][1] -= 1
                    if self.fs[eject][1] > 0:
                        continue
                    self.fssize -= self.fs[eject][0]
                    self.fs.pop(eject, None)
                    self.fsevicts += 1
                self.fs[layer] = [layerSize, 1]
                self.fslmu.append(layer)
                self.fssize += layerSize

    def place(self, request):
        if request[-1] in self.mem:
            self.lmu.append(request[-1])
            self.mem[request[-1]][1] += 1
            self.hits += 1
            if self.first == True:
                self.firstmemhits += 1
            if self.fsfirst == True:
                self.firstfsmemhits += 1
            
        else:
            self.misses += 1
            if self.first == True:
                self.firstMiss += 1

            if request[1] >= self.restrict:
                self.fsPlace(request[-1], request[1])
                return

            self.fsCheck(request)

            if request[1] + self.size <= self.capacity:
                self.mem[request[-1]] = [request[1], 1]
                self.lmu.append(request[-1])
                self.size += request[1]
            else:
                self.first = False
                while request[1] + self.size > self.capacity:
                    eject = self.lmu.pop(0)
                    self.mem[eject][1] -= 1
                    if self.mem[eject][1] > 0:
                        continue
                    self.fsPlace(eject, self.mem[eject][0], ejected=True)
                    self.size -= self.mem[eject][0]
                    self.mem.pop(eject, None)
                    self.evictions += 1

                self.mem[request[-1]] = [request[1], 1]
                self.lmu.append(request[-1])
                self.size += request[1]

    def get_lmu_hits(self):
        return self.hits - self.firstmemhits

    def get_h_hits(self):
        return self.hits + self.fshits - self.firstfsmemhits - self.firstfshits

    def get_lmu_misses(self):
        return self.misses - self.firstMiss

    def get_h_misses(self):
        return self.fsmiss - self.fsfirstMiss

    def get_all(self):
        info = {
            'memory hits': self.hits,
            'memory misses': self.misses,
            'initial memory misses': self.firstMiss,
            'memory evictions': self.evictions,
            'file system hits': self.fshits,
            'file system misses': self.fsmiss,
            'initial file system misses': self.fsfirstMiss,
            'file system evictions': self.fsevicts,
            'initial memory hits': self.firstmemhits,
            'initial memory-file-system hits': self.firstfsmemhits,
            'initial file system hits': self.firstfshits}
        return info


def reformat(indata):
    ret = []
    for item in indata:
        if 'manifest' in item['uri']:
            continue

        layer = item['uri'].split('/')[-1]
        ret.append((item['delay'], item['size'], layer)) # delay: datetime

    return ret

def run_sim(requests, size):
    #print requests
    t = time.time()
    caches = []
    caches.append(complex_cache(size=size, fssize = 10))
    caches.append(complex_cache(size=size, fssize = 15))
    caches.append(complex_cache(size=size, fssize = 20))
    i = 0
    count = 10
    j = 0
    hr_no = 0
    hit_ratio_each_hr = {}
    
    for request in requests:
        j += 1
        if j == 1:
            starttime = request[0][0]
            #print type(starttime)
            #print request[0]
            print "starttime: "+str(starttime)
        #print request[j]
        #print type(request[j])
        #print j
        if int(request[j][0] - starttime) % (60*60) == 0: # calculate for each hr
            hr_no += 1
            hit_ratio_each_hr[str(hr_no) + ' 10 lmu hits'] = caches[i].get_lmu_hits()
            hit_ratio_each_hr[str(hr_no) + ' 10 lmu misses'] = caches[i].get_lmu_misses()
            hit_ratio_each_hr[str(hr_no) + ' 10 h hits'] = caches[i].get_h_hits()
            hit_ratio_each_hr[str(hr_no) + ' 10 h misses'] = caches[i].get_h_misses()
            hit_ratio_each_hr[str(hr_no) + ' 15 lmu hits'] = caches[i + 1].get_lmu_hits()
            hit_ratio_each_hr[str(hr_no) + ' 15 lmu misses'] = caches[i + 1].get_lmu_misses()
            hit_ratio_each_hr[str(hr_no) + ' 15 h hits'] = caches[i + 1].get_h_hits()
            hit_ratio_each_hr[str(hr_no) + ' 15 h misses'] = caches[i + 1].get_h_misses()
            hit_ratio_each_hr[str(hr_no) + ' 20 lmu hits'] = caches[i + 2].get_lmu_hits()
            hit_ratio_each_hr[str(hr_no) + ' 20 lmu misses'] = caches[i + 2].get_lmu_misses()
            hit_ratio_each_hr[str(hr_no) + ' 20 h hits'] = caches[i + 2].get_h_hits()
            hit_ratio_each_hr[str(hr_no) + ' 20 h misses'] = caches[i + 2].get_h_misses()
                
        if 1.*i / len(requests) > 0.1:
            i = 0
            print str(count) + '% done'
            count += 10
        for c in caches:
            c.place(request)
        i += 1
    hit_ratios = {}
    i = 0
    hit_ratios[str(i) + ' 10 lmu hits'] = caches[i].get_lmu_hits()
    hit_ratios[str(i) + ' 10 lmu misses'] = caches[i].get_lmu_misses()
    hit_ratios[str(i) + ' 10 h hits'] = caches[i].get_h_hits()
    hit_ratios[str(i) + ' 10 h misses'] = caches[i].get_h_misses()
    hit_ratios[str(i) + ' 15 lmu hits'] = caches[i + 1].get_lmu_hits()
    hit_ratios[str(i) + ' 15 lmu misses'] = caches[i + 1].get_lmu_misses()
    hit_ratios[str(i) + ' 15 h hits'] = caches[i + 1].get_h_hits()
    hit_ratios[str(i) + ' 15 h misses'] = caches[i + 1].get_h_misses()
    hit_ratios[str(i) + ' 20 lmu hits'] = caches[i + 2].get_lmu_hits()
    hit_ratios[str(i) + ' 20 lmu misses'] = caches[i + 2].get_lmu_misses()
    hit_ratios[str(i) + ' 20 h hits'] = caches[i + 2].get_h_hits()
    hit_ratios[str(i) + ' 20 h misses'] = caches[i + 2].get_h_misses()

    return hit_ratios

def init(data, args):
    cache_size = args['cache_size']

    print 'running cache simulation'

    parsed_data = reformat(data)
    print 'parsed_data len' + str(len(parsed_data))
    info = run_sim(parsed_data, cache_size)

    for thing in info:
        print thing + ': ' + str(info[thing])


############## Keren ###############
def count(data):
    size = 0
    for req in data:
        size += req['size']

    args = {'cache_size': size}
    return args

def get_requests(files, t, limit):
    ret = []
    requests = []
    for filename in files:
        print filename
        with open(filename, 'r') as f:
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
                    #blob = request['data']
                    r = {
                        'delay': timestamp, 
                        'uri': uri, 
                        'size': size, 
                        'method': method, 
                        'duration': duration,
                        'client': client,
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

def main():
    parser = ArgumentParser(description='arg pser.')
    #parser.add_argument('-t', '--trace', dest='traces', type=str, required=True, help = 'traces')
    parser.add_argument('-c', '--config', dest='configs', type=str, required=True, help = 'configs')

    arguments = parser.parse_args()

    #print 'try start'
    config = file(arguments.configs, 'r')
    try:
        inputs = yaml.load(config)
    except Exception as inst:
        print 'error reading config file'
	print inst
        exit(-1)
    config.close()

    if 'trace' not in inputs:
        print 'trace field required in config file'
        exit(1)

    limit_type = None
    limit = 0

    trace_files = []

    if 'location' in inputs['trace']:
        location = inputs['trace']['location']
        if '/' != location[-1]:
            location += '/'
        for fname in inputs['trace']['traces']:
            trace_files.append(location + fname)
    else:
        trace_files.extend(inputs['trace']['traces'])


    if 'limit' in inputs['trace']:
        limit_type = inputs['trace']['limit']['type']
        if limit_type in ['seconds', 'requests']:
            limit = inputs['trace']['limit']['amount']
        else:
            print 'Invalid trace limit_type: limit_type must be either seconds or requests'
            exit(1)
    else:
        print 'limit_type not specified, entirety of trace files will be used will be used.'


    print 'starting to read trace files...'
    json_data = get_requests(trace_files, limit_type, limit)
    print 'json_data len: ' + str(len(json_data))
    if json_data is None:
        print 'empty json'
        exit(1)
    args = count(json_data)
    init(json_data, args)


if __name__ == "__main__":
    main()
