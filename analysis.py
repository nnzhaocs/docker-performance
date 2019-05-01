import sys
import traceback
import socket
import os
from argparse import ArgumentParser
import requests
import time
import datetime
import random
import threading
import multiprocessing
import json 
import yaml
from dxf import *
from multiprocessing import Process, Queue
import importlib
import hash_ring
from collections import defaultdict
from audioop import avg
import statistics
import numpy
from __builtin__ import str
from Carbon.Aliases import false

input_dir = '/home/nannan/dockerimages/docker-traces/data_centers/'

####
# Random match
####

def get_requests(trace_dir):
    print "walking trace_dir: "+trace_dir
    absFNames = absoluteFilePaths(trace_dir)

    blob_locations = []
#     tTOblobdic = {}
#     blobTOtdic = {}
    ret = []
#     i = 0
    
#     for location in realblob_locations:
#         absFNames = absoluteFilePaths(location)
    print "Dir: "+trace_dir+" has the following files"
    print absFNames
    blob_locations.extend(absFNames)
    
    for trace_file in blob_locations:
        with open(trace_file, 'r') as f:
            requests = json.load(f)
            
        for request in requests:
            
            method = request['http.request.method']
            uri = request['http.request.uri']
    	    if len(uri.split('/')) < 3:
                continue
            # ignore othrs reqs, because using push and pull reqs.
            if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):
                size = request['http.response.written']
                if size > 0:
#                     timestamp = datetime.datetime.strptime(request['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
#                     duration = request['http.request.duration']
#                     client = request['http.request.remoteaddr']
            
#                     for blob in blob_locations:
#                     if i < len(blob_locations):
#                         blob = blob_locations[i]
                        #uri = request['http.request.uri']
#                         if layer_id in tTOblobdic.keys():
#                             continue
#                         if blob in blobTOtdic.keys():
#                             continue
                        
#                         tTOblobdic[layer_id] = blob
#                         blobTOtdic[blob] = layer_id

#                         size = os.stat(blob).st_size
                
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
                            "timestamp": request['timestamp']
#                             'data': blob
                        }
                        print r
                        ret.append(r)
#                         i += 1
#     return ret 
    ret.sort(key= lambda x: x['timestamp'])                          
    with open(os.path.join(input_dir, 'total_trace.json'), 'w') as fp:
        json.dump(ret, fp)      
        

def analyze_layerlifetime():
    
    layerPUTGAcctimedic = defaultdict(list)
    layerNPUTGAcctimedic = defaultdict(list)
    layerNGETAcctimedic = {}
    
    layer1stPUT = -1
#     layer1stGET = -1
    layerNPUT = False
    layerNGET = False
#     layecntGET = 0
    
    with open(os.path.join(input_dir, 'layer_access.json')) as fp:
        layerTOtimedic = json.load(fp)

    for k in sorted(layerTOtimedic, key=lambda k: len(layerTOtimedic[k]), reverse=True):
         
        #lifetime = layerTOtimedic[k][len(layerTOtimedic[k][0])-1][1] - layerTOtimedic[k][0][1]
        #lifetime = lifetime.total_seconds()
           
        lst = layerTOtimedic[k]
        
        if 'PUT' == lst[0][0]:
            layer1stPUT = 0
            if len(lst) == 1:
                layerNGET = True
        else:
            layerNPUT = True
            
        if True == layerNGET:
            layerNGETAcctimedic[k] = True
            continue
        
        starttime = lst[0][1]#datetime.datetime.strptime(lst[0][1], '%Y-%m-%dT%H:%M:%S.%fZ')
        interaccess = ((starttime),)
        #interaccess = interaccess + (k,)
        # (digest, next pull time)
        
        for i in range(len(lst)-1):
            nowtime = datetime.datetime.strptime(lst[i][1], '%Y-%m-%dT%H:%M:%S.%fZ')#lst[i][1]
            nexttime = datetime.datetime.strptime(lst[i+1][1], '%Y-%m-%dT%H:%M:%S.%fZ')#lst[i+1][1]
            delta = nexttime - nowtime
            delta = delta.total_seconds()
            
            interaccess = interaccess + (delta,)                   
                    
        if -1 == layer1stPUT:
            layerNPUTGAcctimedic[k] = interaccess
        else:
            layerPUTGAcctimedic[k] = interaccess

    if layerNGETAcctimedic:
        with open(os.path.join(input_dir, 'layerNGETAcctime.json'), 'w') as fp:
            json.dump(layerNGETAcctimedic, fp)
    if layerNPUTGAcctimedic:
        with open(os.path.join(input_dir, 'layerNPUTAcctime.json'), 'w') as fp:
            json.dump(layerNPUTGAcctimedic, fp)
    if layerPUTGAcctimedic:
         with open(os.path.join(input_dir, 'layerPUTGAcctime.json'), 'w') as fp:
             json.dump(layerPUTGAcctimedic, fp)


def analyze_requests(total_trace):
    organized = []
    layerTOtimedic = defaultdict(list)
    
#     start = ()

#     if round_robin is False:
#         ring = hash_ring.HashRing(range(numclients))
    with open(total_trace, 'r') as f:
        blob = json.load(f)

#     for i in range(numclients):
#         organized.append([{'port': port, 'id': random.getrandbits(32), 'threads': client_threads, 'wait': wait, 'registry': registries, 'random': push_rand}])
#         print organized[-1][0]['id']
#     i = 0

    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        
        if 'blob' in uri:
            # uri format: v2/<username>/<repo name>/[blobs/uploads | manifests]/<manifest or layer id>
            layer_id = uri.rsplit('/', 1)[1]
            timestamp = r['timestamp']
    #        timestamp = datetime.datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
            method = r['http.request.method']
        
            print "layer_id: "+layer_id
            print "repo_name: "+repo_name
            print "usrname: "+usrname
            
    #         if layer_id in layerTOtimedic.keys():
            layerTOtimedic[layer_id].append((method, timestamp))
        
    with open(os.path.join(input_dir, 'layer_access.json'), 'w') as fp:
        json.dump(layerTOtimedic, fp)
        

def analyze_repo_reqs(total_trace):
#     organized = []
    usrTOrepoTOlayerdic = defaultdict(list) # repoTOlayerdic
    repoTOlayerdic = defaultdict(list)
    usrTOrepodic = defaultdict(list) # repoTOlayerdic
    
#     start = ()

#     if round_robin is False:
#         ring = hash_ring.HashRing(range(numclients))
    with open(total_trace, 'r') as f:
        blob = json.load(f)

#     for i in range(numclients):
#         organized.append([{'port': port, 'id': random.getrandbits(32), 'threads': client_threads, 'wait': wait, 'registry': registries, 'random': push_rand}])
#         print organized[-1][0]['id']
#     i = 0

    # get usr -> repo -> layer map

    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name
        
        if 'blob' in uri:
            layer_id = uri.rsplit('/', 1)[1]
            timestamp = r['timestamp']
    #        timestamp = datetime.datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
            method = r['http.request.method']
        
            print "layer_id: "+layer_id
            print "repo_name: "+repo_name
            print "usrname: "+usrname
            
            if repo_name in repoTOlayerdic.keys():
                if layer_id not in repoTOlayerdic[repo_name]:
                    repoTOlayerdic[repo_name].append(layer_id)
            else:
                repoTOlayerdic[repo_name].append(layer_id)
                
            
#             try:
#                 lst = repoTOlayerdic[repo_name]
#                 if layer_id not in lst:
#                     repoTOlayerdic[repo_name].append(layer_id)
#             except Exception as e:
#                 print "repo has not this layer before"
#                 repoTOlayerdic[repo_name].append(layer_id)

            #if 
                
            try:
                lst = usrTOrepodic[usrname]
                if repo_name not in lst:
                    usrTOrepodic[usrname].append(repo_name)
            except Exception as e:
                print "usrname has not this repo before"
                usrTOrepodic[usrname].append(repo_name)
#             if layer_id
            
    #         if layer_id in layerTOtimedic.keys():
            #layerTOtimedic[layer_id].append((method, timestamp))
#             repoTOlayerdic[repo_name].append(layer_id)

    for repo in repoTOlayerdic.keys():
        jsondata = {
            ''
        }

    for usr in usrTOrepodic.keys():
        for repo in usrTOrepodic[usr]:
            usrTOrepoTOlayerdic[usr].append({repo:repoTOlayerdic[repo]})
            
    for usr in usrTOrepodic.keys():
        jsondata = {
            'usr': usr,
            'repos': usrTOrepoTOlayerdic[usr]
            
        }
        
    with open(os.path.join(input_dir, 'usr2repo2layer_map.json'), 'w') as fp:
        json.dump(usrTOrepoTOlayerdic, fp)


def analyze_usr_repolifetime():
#     layerPUTGAcctimedic = defaultdict(list)  # 
#     layerNPUTGAcctimedic = defaultdict(list) #
#     layerNGETAcctimedic = {}
    
#     layer1stPUT = -1
# #     layer1stGET = -1
#     layerNPUT = False
#     layerNGET = False
#     layecntGET = 0
    
    with open(os.path.join(input_dir, 'usr2repo2layer_map.json')) as fp:
        usrrepolayer_map = json.load(fp)

#     with open(os.path.join(input_dir, 'layer_access.json')) as fp:
#         layerTOtimedic = json.load(fp)

#     for k in sorted(layerTOtimedic, key=lambda k: len(layerTOtimedic[k]), reversed=True):
#          
#         lifetime = layerTOtimedic[k][len(layerTOtimedic[k][0])-1][1] - layerTOtimedic[k][0][1]
#         lifetime = lifetime.total_seconds()
#            
#         lst = layerTOtimedic[k]
#         
#         if 'PUT' == lst[0][0]:
#             layer1stPUT = 0
#             if len(lst) == 1:
#                 layerNGET = True
#         else:
#             layerNPUT = True
#             
#         if False == layerNGET:
#             layerNGETAcctimedic[k] = True
#             continue
#         
#         interaccess = ((),)
#         #interaccess = interaccess + (k,)
#         # (digest, next pull time)
#         
#         for i in len(lst)-2:
#             nowtime = lst[i][1]
#             nexttime = lst[i+1][1]
#             delta = nexttime - nowtime
#             delta = delta.total_seconds()
#             
#             interaccess = interaccess + (delta,)                   
#                     
#         if -1 == layer1stPUT:
#             layerNPUTGAcctimedic[k] = interaccess
#         else:
#             layerPUTGAcctimedic[k] = interaccess

#     if layerNGETAcctimedic:

    NlayerPUTGAcctimedic = 0
    NlayerNPUTGAcctimedic = 0
    NlayerNGETAcctimedic = 0
    
    repoTOlayerdic = {} #defaultdict(list)
    
#     userTOlayerdic = defaultdict(list)

    with open(os.path.join(input_dir, 'layerNGETAcctime.json')) as fp1:
        layerNGETAcctimedic = json.load(fp1)
#     if layerNPUTGAcctimedic:
    with open(os.path.join(input_dir, 'layerNPUTAcctime.json')) as fp2:
        layerNPUTGAcctimedic = json.load(fp2)
#     if layerPUTGAcctimedic:
    with open(os.path.join(input_dir, 'layerPUTGAcctime.json')) as fp3:
         layerPUTGAcctimedic = json.load(fp3)
    #cnt = 0
    for usr in usrrepolayer_map.keys():   
        #cnt += 1
        #if cnt > 100:
        #    break;     
#         usrTOrepodic = defaultdict(list) # repoTOlayerdic
#         repoTONPUTAlayerdic = defaultdict(list)
#         repoTONGETAlayerdic = defaultdict(list)
        print "process usr "+usr
        for repo_item in usrrepolayer_map[usr]:  
            for repo, layers in repo_item.items():                         
                if repo in repoTOlayerdic.keys():
			continue
                print "process repo "+repo
                #cnt += 1
		#if cnt > 1000:
		   
                #repoTOPUTGAlayerdic = defaultdict(list) # repoTOlayerdic
                #repoTONPUTAlayerdic = defaultdict(list)
                #repoTONGETAlayerdic = defaultdict(list)
                
#                 repodic = defaultdict(list)
                repodic = {
                        'layerPUTGAlayerdic': [],
                        'layerNPUTGAcctimedic': [],
                        'layerNGETAlayerdic': []
                    }
            
                for layer in layers:#repo.keys():
                    if layer in layerPUTGAcctimedic.keys():
                        NlayerPUTGAcctimedic = 1
                        lst = layerPUTGAcctimedic[layer]
                    elif layer in layerNPUTGAcctimedic.keys():
                        NlayerNPUTGAcctimedic = 1
                        lst = layerNPUTGAcctimedic[layer]
                    elif layer in layerNGETAcctimedic.keys():
                        NlayerNGETAcctimedic = 1
                        lst = layerNGETAcctimedic[layer]
                    else:
                        print "cannot find the layer: "+layer 
                        continue                            
                    
#                     if NlayerPUTGAcctimedic and NlayerNPUTGAcctimedic and NlayerNGETAcctimedic:
#                         print "this is not a legal layer"
#                         continue
                    if NlayerPUTGAcctimedic == 1:
                        print "this is a layerPUTGAcctimedic "+layer
#                         repoTOPUTGAlayerdic[layer].append(lst)
                        repodic['layerPUTGAlayerdic'].append({layer: lst}) 
                    elif NlayerNPUTGAcctimedic == 1:
                        print "this is a layerNPUTGAcctimedic "+layer
#                         repoTONPUTAlayerdic[layer].append(lst)
                        repodic['layerNPUTGAcctimedic'].append({layer: lst})
                    elif NlayerNGETAcctimedic == 1:
                        print "this is a layerNGETAcctimedic "+layer
#                         repoTONGETAlayerdic[layer].append(lst)
                        repodic['layerNGETAlayerdic'].append({layer: lst})
                        
            repoTOlayerdic[repo] = repodic
        
#             repoTOlayerdic[repo]['repoTOPUTGAlayerdic'] =  repodic['repoTOPUTGAlayerdic']
#             repoTOlayerdic[repo]['repoTONPUTAlayerdic'] =  repodic['repoTONPUTAlayerdic']
#             repoTOlayerdic[repo]['repoTONGETAlayerdic'] =  repodic['repoTONGETAlayerdic']
            
    with open(os.path.join(input_dir, 'repo2layersaccesstime.json'), 'w') as fp:
        json.dump(repoTOlayerdic, fp)           
                    
         
def clusterUserreqs(total_trace):
    organized = defaultdict(list)
    with open(total_trace, 'r') as f:
        blob = json.load(f)
    for r in blob:
        #timestamp = datetime.datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        request = {
            'delay': r['timestamp'],
            'duration': r['http.request.duration'],
            'uri': r['http.request.uri'],
            'clientAddr': r['http.request.remoteaddr'],
            'method':r['http.request.method'],
        }
 
        clientAddr = r['http.request.remoteaddr']
        print request
        organized[clientAddr].append(request)
    return organized
 
 
def clusterClientReqs(total_trace):
    organized = defaultdict(list)

    organized = clusterUserreqs(total_trace)     
     
    img_req_group = []
    for cli, reqs in organized.items():
        cli_img_req_group = [[]]
        prev = cli_img_req_group[-1]
        cur = []
#         prev_push = []
#         cur_push = []
        for req in reqs:
            uri = req['uri'] 
            layer_or_manifest_id = uri.rsplit('/', 1)[1]
            parts = uri.split('/')
            repo = parts[1] + '/' + parts[2]
	    #prev = cli_img_req_group[-1]
            if req['method'] == 'GET':
                print 'GET: '+'uri'
                if 'blobs' in uri:
                    print 'GET layer'
                    prev.append(req)
                else:
                    print 'GET manifest'
                    cur = []
                    cur.append(req)
                    cli_img_req_group.append(cur)
                    prev = cli_img_req_group[-1]
#             else:
#                 print 'PUT: '+'uri'
#                 if 'blobs' in uri:
#                     print 'PUT layer'
#                     prev_push.append(req)
#                 elif 'manifests' in uri:
#                     print 'PUT manifest'
#                     prev_push.append(req)
#                     cur_push = []
#                     cli_img_push_group.append(cur_push)
#                 prev_push = cli_img_push_group[-1]
                 
#         cli_img_req_group = cli_img_pull_group + cli_img_push_group
	cli_img_req_group_new = [x for x in cli_img_req_group if x]
	print cli_img_req_group_new
        #cli_img_req_group.sort(key= lambda x: x[0]['delay'])
        img_req_group += cli_img_req_group_new
    img_req_group.sort(key= lambda x: x[0]['delay'])
#     return img_req_group
    with open('sorted_reqs.lst', 'w') as fp:
        json.dump(img_req_group, fp)    
#     return organized
 

#                               
def durationmanifestblobs():
    with open('sorted_reqs.lst', 'r') as fp:
        blob = json.load(fp)
        
    intervals_GET_MLs = []
    lst = []
    for r in blob:
        rintervals_GET_ML = []
        delay_GET_Ls=[]
        
        if (r[0]['method'] != 'GET') or ('manifest' not in r[0]['uri']):
            continue
        if len(r) < 2:
            continue
        
        delay_GET_M = datetime.datetime.strptime(r[0]['delay'], '%Y-%m-%dT%H:%M:%S.%fZ')  
         
        for i in range(1,len(r)):
            delay_GET_Ls.append(datetime.datetime.strptime(r[i]['delay'], '%Y-%m-%dT%H:%M:%S.%fZ'))
            
        for j in delay_GET_Ls:
            delta = j - delay_GET_M
            delta = delta.total_seconds()
            rintervals_GET_ML.append(delta)
    	print rintervals_GET_ML
        intervals_GET_MLs.append(rintervals_GET_ML)
        lst.extend(rintervals_GET_ML)
    print "avg interval between a get manifest and a get layer:" + str(sum(lst)*1.0 / len(lst)) 
    print "midian is:  "+ str(statistics.median(lst))  
    
    with open('intervals_client_GET_MLs.lst', 'w') as fp:
        json.dump(intervals_GET_MLs, fp)
    with open('intervals_GET_MLs.lst', 'w') as fp:
        json.dump(lst, fp)  


def numpy_fillna(data):
    # Get lengths of each row of data
    lens = numpy.array([len(i) for i in data])

    # Mask of valid places in each row
    mask = numpy.arange(lens.max()) < lens[:,None]

    # Setup output array and put elements from data into masked positions
    out = numpy.zeros(mask.shape, dtype=data.dtype)
    out[mask] = numpy.concatenate(data)
    return out


def calbatchstats():
    with open('intervals_GET_MLs.lst', 'r') as fp: 
        data = json.load(fp)
    
    all_intervals = numpy.array(data)
    print "all intervals:====>"
    print "50 percentile: "+str(numpy.percentile(all_intervals, 50))
    print "75 percentile: "+str(numpy.percentile(all_intervals, 75))
    print "99 percentile: "+str(numpy.percentile(all_intervals, 99))
    print "max: "+str(numpy.amax(all_intervals))
    print "min: "+str(numpy.amin(all_intervals))
    
    with open('intervals_client_GET_MLs.lst', 'r') as fp:
        data = json.load(fp)
    
    client_img_pull_intervals = numpy.array(data, dtype=object)
    out = numpy_fillna(data)
    len = out.shape[1]
    num_arrays = 0
    if len % 3 == 0:
        num_arrays = len/3
    else:
        num_arrays = len/3 + 1
    array_lst = out.array_split(out, num_arrays)
    i = 1
    outputstat = []
    for ar in array_lst:
#         lst = ar.tolist()
#         ar_lst = numpy.array(lst)
        ar_lst_nozeros = numpy.ma.masked_equal(ar_lst).compressed()
#         tmp = []
        print "batch intervals:====> "+str(i)+" batch"
        print "avg: "+ str(numpy.average(ar_lst_nozeros))
        print "50 percentile: "+str(numpy.percentile(ar_lst_nozeros, 50))
        print "75 percentile: "+str(numpy.percentile(ar_lst_nozeros, 75))
        print "99 percentile: "+str(numpy.percentile(ar_lst_nozeros, 99))
        print "max: "+str(numpy.amax(ar_lst_nozeros))
        print "min: "+str(numpy.amin(ar_lst_nozeros))
        outputstat.append([numpy.average(ar_lst_nozeros), numpy.percentile(ar_lst_nozeros, 50), numpy.percentile(ar_lst_nozeros, 75), numpy.percentile(ar_lst_nozeros, 99), numpy.amax(ar_lst_nozeros), numpy.amin(ar_lst_nozeros)])
        i += 1
    with open('batch_intervalstat_avg_50_75_99_max_min.lst', 'w') as fp:
        json.dump(outputstat, fp)  
        
#     for i in range(0, len, 3):
#         batch = out[:,1:len:3]

def repullLayers(total_trace):
    with open(total_trace, 'r') as fp:
        blob = json.load(fp)
    
    clientTOlayerMap = defaultdict(list)
        
    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name
        
        clientAddr = r['http.request.remoteaddr']
        method = r['http.request.method']
        
        if ('blobs' in uri) and ('GET' == method):
            layer_id = uri.rsplit('/', 1)[1]
                    
            print "layer_id: "+layer_id
#             print "repo_name: "+repo_name
             
            find = False    
            try:
                lst = clientTOlayerMap[clientAddr]
                for tup in lst:
                    if tup[0] == layer_id:
                        find = True
                        newtup = (layer_id, tup[1]+1)
                        clientTOlayerMap[clientAddr].append(newtup)
                        print clientAddr + ', ' + layer_id + ', ' + str(tup[1]+1)
                        break
                    
                if not find:
                    print "usrname has not this layer before"
                    clientTOlayerMap[clientAddr].append((layer_id, 0))   
                    print  clientAddr + ', ' + layer_id + ', ' + str(0)              
            except Exception as e:
                print "usrname has not this layer before"
                clientTOlayerMap[clientAddr].append((layer_id, 0))
                print  clientAddr + ', ' + layer_id + ', ' + str(0)

    repulledlayer_cnt = 0
    totallayer_cnt = 0
 
    for cli in clientTOlayerMap.keys():
        for tup in cli:
            totallayer_cnt += 1
            if tup[1]:
                repulledlayer_cnt += 1
                

    print "totallayer_cnt:    " + str(totallayer_cnt) 
    print "repulledlayer_cnt:   " + str(repulledlayer_cnt)
    print "ratio:  " + str(1.0*totallayer_cnt/repulledlayer_cnt)

    with open('client_to_layer_map.json', 'w') as fp:
        json.dump(clientTOlayerMap, fp) 

def main():

    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input YAML configuration file, should contain all the inputs requried for processing')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, help= 'Trace player command. Possible commands: warmup, run, simulate, warmup is used to populate the registry with the layers of the trace, run replays the trace, and simulate is used to test different caching and prefecting policies.')

    args = parser.parse_args()
    
    trace_dir = input_dir+args.input
    
    print "input dir: "+trace_dir
    
    #NANNAN
    if args.command == 'get':    
#         if 'realblobs' in inputs['client_info']:
            #if inputs['client_info']['realblobs'] is True:
#             realblob_locations = inputs['client_info']['realblobs']
        get_requests(trace_dir)
        return
	    #else:
		#print "please put realblobs!"
		#return
    elif args.command == 'Alayer':
#         print "wrong cmd!"
        analyze_requests(os.path.join(input_dir, 'total_trace.json'))
        return 
    elif args.command == 'layerlifetime':
        analyze_layerlifetime()
        return
    elif args.command == 'map':
        analyze_repo_reqs(os.path.join(input_dir, 'total_trace.json'))
        return
    elif args.command == 'repolayer':
        analyze_usr_repolifetime()
    elif args.command == 'clusteruserreqs':
        clusterClientReqs(os.path.join(input_dir, 'total_trace.json'))
    elif args.command == 'calintervalgetML':
        durationmanifestblobs()
    elif args.command == 'calbatchstats':
        calbatchstats()
    elif args.command == 'repullLayers':
        repullLayers(os.path.join(input_dir, 'total_trace.json'))
        return
    

if __name__ == "__main__":
    main()
