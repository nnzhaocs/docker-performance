import time
import math
import pdb
import datetime
from lru import LRU
import json

    
class complex_cache:
    def __init__(self, size): # the number of items
        self.size = size # actual size of the cache
        self.repo_lru = LRU(size)
        self.user_lru = LRU(10000)

        self.hits = 0.0
        self.reqs = 0.0
        self.repo_set = set()
        self.cache_stack_size = 0 # how much of the cache is occupied


    def place(self, request):
        # request is a tuple (timestamp, layerid, size)
        self.reqs += 1 
        self.repo_set.add(request['repo'])
        if self.repo_lru.has_key(request['repo']): 
            self.repo_lru[request['repo']]['clients'].add(request['client'])
            self.repo_lru[request['repo']]['layers'].add((request['layer'], request['size']))
            self.repo_lru[request['repo']]['count'] += 1
            if self.user_lru.has_key(request['client']):
                self.user_lru[request['client']] += 1
            else:
                self.user_lru[request['client']] = 1
            
            self.hits += 1            
        else:
            all_items = self.repo_lru.items()
            index = len(all_items) - 1
            while self.cache_stack_size + 1 > self.size and index >= (len(all_items)/2): 
                # pdb.set_trace()
                item_to_check = all_items[index] # gets the key
                # first 10 percent
                item_clients = item_to_check[1]['clients']
                all_clients = self.user_lru.keys()
                two_percent = int(math.ceil((len(all_clients)/100.0)*2))

                all_clients_2_percent = set(all_clients[:two_percent]) # the first 2 percent of the clients in MRU order
                if item_clients.intersection(all_clients_2_percent):
                    index -= 1
                    continue

                self.cache_stack_size -= 1
                del self.repo_lru[item_to_check[0]]
                index -= 1
                
            if self.cache_stack_size + 1 > self.size:
                # pdb.set_trace()
                remove = self.repo_lru.peek_last_item()[0]
                del self.repo_lru[remove]
                self.cache_stack_size -= 1
                
            self.repo_lru[request['repo']] = {'clients': set(), 'count': 0, 'layers': set() }
            self.repo_lru[request['repo']]['clients'].add(request['client'])
            self.repo_lru[request['repo']]['layers'].add((request['layer'], request['size']))
            self.repo_lru[request['repo']]['count'] += 1
            if self.user_lru.has_key(request['client']):
                self.user_lru[request['client']] += 1
            else:
                self.user_lru[request['client']] = 1
            self.cache_stack_size += 1
            

def extract(data):
  
    requests = []

    for request in data:
        size = request['http.response.written']

        method = request['http.request.method']
        uri = request['http.request.uri']
        if 'manifests' in uri or 'PUT' in method:
            continue
        timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # uri format: v2/<username>/<repo name>/[blobs/uploads | manifests]/<manifest or layer id>
        parts = uri.split('/')
        requests.append({'timestamp': timestamp, 
                        'client': request['http.request.remoteaddr'], 
                        'method': request['http.request.method'], 
                         'repo': parts[1]+'/'+parts[2],
                         'layer': parts[-1],
                         'size': size,
        })
    return requests

# 5%, 10%, 15%, 20%, 25%, 30%, 40%, 50%
# usrs: 9,997 
# repos: 40,264
# layers: 829,202

def run_sim(requests, portion):
       
    print portion
    size1 = 50
    
    caches = []
    caches.append(complex_cache(size1))
    
    i = 0
    count = 10
    j = 0
    hr_no = 0
    
    for request in requests:
        for c in caches:
            c.place(request)
        #if interval > 1 and interval % (60 * 60) == 0:
            #pdb breakpoint here
            #pdb.set_trace()
                
        if 1.*i / len(requests) > 0.1:
            i = 0
            print str(count) + '% done'
            count += 10
        i += 1

    repo_lru_size = sum([sum([item[1] for item in repo[1]['layers']])
                         for repo in caches[0].repo_lru.items()])
    total_hit_ratio = {"hit_ratio": caches[0].hits/caches[0].reqs,
                       "repo lru length": len(caches[0].repo_lru.keys()),
                       "client lru size": len(caches[0].user_lru.keys()),
                       "unique repos": len(caches[0].repo_set),
                       "repo lru size in bytes": repo_lru_size,
                       }

    return total_hit_ratio


def init(data, portion=100):

    # outputfile = 
    parsed_data = extract(data)
    total_hit_ratio = run_sim(parsed_data, portion)
    
    with open("Repo_LRU_list_dal09.json", 'a') as fp:
        fp.write(str(portion)+"% trace\n")
        json.dump(total_hit_ratio, fp)
        fp.write("\n\n")

#     for thing in info:
#         print thing + ': ' + str(info[thing])
