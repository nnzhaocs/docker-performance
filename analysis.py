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
#from Carbon.Aliases import false
from sqlitedict import SqliteDict

input_dir = '/home/nannan/dockerimages/docker-traces/data_centers/'


def absoluteFilePaths(directory):
    absFNames = []
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            absFNames.append(os.path.abspath(os.path.join(dirpath, f)))

    return absFNames


def get_requests(trace_dir):
    print "walking trace_dir: "+trace_dir + "and combine them together into a single total json file"
    absFNames = absoluteFilePaths(trace_dir)
    dirname = os.path.basename(trace_dir)
    blob_locations = []

    ret = []

    print "Dir: "+trace_dir+" has the following files"
    print "The output file would be: "+trace_dir+dirname+'_total_trace.json'
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
                        }
                        print r
                        ret.append(r)

    ret.sort(key= lambda x: x['timestamp'])
    with open(os.path.join(input_dir, dirname+'_total_trace.json'), 'w') as fp:
        json.dump(ret, fp)


def getTimeIntervals(total_trace, fname2, fnameout):
    interaccess = []
    fname = os.path.basename(total_trace)
    with open(os.path.join(input_dir, fname + fname2), 'r') as fp:
        usrrepoTOtimedic = json.load(fp)
        
    f = open(input_dir +'temperalTrend/' + fname + fnameout+'.lst', 'w')
    
    for k in sorted(usrrepoTOtimedic, key=lambda k: len(usrrepoTOtimedic[k]), reverse=True):

        lst = usrrepoTOtimedic[k]

        if 1 == len(lst):
            continue 

        for i in range(len(lst)-1):
            nowtime = datetime.datetime.strptime(lst[i], '%Y-%m-%dT%H:%M:%S.%fZ')#lst[i][1]
            nexttime = datetime.datetime.strptime(lst[i+1], '%Y-%m-%dT%H:%M:%S.%fZ')#lst[i+1][1]
            delta = nexttime - nowtime
            delta = delta.total_seconds()
            
            interaccess.append(delta)
            f.write(str(delta)+'\t\n')

    with open(os.path.join(input_dir, fname + fnameout+'.json'), 'w') as fp:
        json.dump(interaccess, fp)
    f.close()


def getSkewness(total_trace):
    print 'start'
    lfname = '-layer_access_cnt.json'
    urfname = '-repo_access_cnt.json'
    ufname = '-usr_access_cnt.json'
    lfoutname = '-layer_access_cnt'
    urfoutname = '-repo_access_cnt'
    ufoutname = '-usr_access_cnt'
    
    getCnt_layer(total_trace, lfname, lfoutname)
    #pullSizeRelationAnalyze(total_trace)

    getCnt(total_trace, urfname, urfoutname)
    getCnt(total_trace, ufname, ufoutname) 
    fname = os.path.basename(total_trace)
    with open(os.path.join(input_dir, fname + '-usr_access_repo_cnt.json'), 'r') as fp:
        usrrepoTOtimedic = json.load(fp)
        
    f = open(input_dir +'temperalTrend/' + fname + '-usr_access_repo_cnt'+'.lst', 'w') 
    fratio = open(input_dir +'temperalTrend/' + fname + '-usr_access_repo_cnt_ratio'+'.lst', 'w')       
    for k in usrrepoTOtimedic:
        lst = usrrepoTOtimedic[k]
        val = len(lst)
        f.write(str(val)+'\t\n')
        sum = 0
        for tup in lst:
            sum += tup[1]
        for tup in lst:
            ratio = (tup[1]*1.0)/sum
            fratio.write(str(ratio)+'\t\n')
            
    f.close()
    fratio.close()
    print 'end' 

    
def getCnt(total_trace, fname2, fnameout):
    print 'in get count'
    interaccess = []
    fname = os.path.basename(total_trace)
    with open(os.path.join(input_dir, fname + fname2), 'r') as fp:
        usrrepoTOtimedic = json.load(fp)
        
    f = open(input_dir +'temperalTrend/' + fname + fnameout+'.lst', 'w')   
     
    
    for k in usrrepoTOtimedic:
        val = usrrepoTOtimedic[k]
        f.write(str(val) + '\t\n')
    f.close()
        
def getCnt_layer(total_trace, fname2, fnameout):
    print 'in get count'
    interaccess = []
    fname = os.path.basename(total_trace)
    with open(os.path.join(input_dir, fname + fname2), 'r') as fp:
        usrrepoTOtimedic = json.load(fp)

    f = open(input_dir +'temperalTrend/' + fname + fnameout+'.lst', 'w')


    for k in usrrepoTOtimedic:
        val = usrrepoTOtimedic[k]
        f.write(str(val[0])+'\t' + str(val[1]) + '\t\n')
    f.close()

def pullSizeRelationAnalyze(total_trace):
    print 'in calculation'
    data = []
    fname = os.path.basename(total_trace)
    with open(os.path.join(input_dir, fname + '-layer_access_cnt.json'), 'r') as fp:
        usrrepoTOtimedic = json.load(fp)

    keys = sorted(usrrepoTOtimedic, key = (lambda x : usrrepoTOtimedic[x]))
    for k in keys:#usrrepoTOtimedic:
        data.append(usrrepoTOtimedic[k])
    
    cnts = sorted(set([elem[0] for elem in data]))


    for cnt in cnts:
        subdt = [elem[1] for elem in data if elem[0] == cnt]
        total = sum(subdt)
        try:
            avg = total/len(subdt)
        except:
            avg = 0
        print 'For hit count of ' + str(cnt) + ': '
        if cnt == 0:
            cnt = 1
        print 'number of layers = ' + str(len(subdt)) + '; total size = ' + str(total) + '; average size = ' + str(avg) + '; hit/avg size ratio = '+ str(avg/cnt)
        print 'max = ' + str(subdt[-1]) + ', min = ' + str(subdt[0])
        
def analyze_reusetime(total_trace):
    
    lfname = '-layer_access_timestamp.json'
    urfname = '-usrrepo_access_timestamp.json'
    ufname = '-usr_access_timestamp.json'
    lfoutname = '-layer-raccessinterval'
    urfoutname = '-usrrepo-raccessinterval'
    ufoutname = '-usr-raccessinterval'
    getTimestamp(total_trace)
    
    getTimeIntervals(total_trace, lfname, lfoutname)
    getTimeIntervals(total_trace, urfname, urfoutname)
    getTimeIntervals(total_trace, ufname, ufoutname)
    
    
def getTimestamp(total_trace):
    layerTOtimedic = defaultdict(list)
    usrrepoTOtimedic = defaultdict(list)
    usrTOtimedic = defaultdict(list)
    
    layerToCcntdic = {}
    repoToCcntdic = {}
    usrToCcntdic = {}
    
    usrTorepocntdic = defaultdict(list)
    
    fname = os.path.basename(total_trace)
    
    print "the output file would be: " + input_dir + fname + '-layer_access_timestamp.json'
    print "the output file would be: " + input_dir + fname + '-usrrepo_access_timestamp.json'
    print "the output file would be: " + input_dir + fname + '-usr_access_timestamp.json'
    
    with open(total_trace, 'r') as f:
        blob = json.load(f)

    for r in blob:
        uri = r['http.request.uri']
        method = r['http.request.method']
        clientAddr = r['http.request.remoteaddr']
        timestamp = r['timestamp']
        size = r['http.response.written']
 
        layer_id_or_manifest_id = uri.rsplit('/', 1)[1]
            
        repo_namepart1 = uri.split('/')[1]
        repo_namepart2 = uri.split('/')[2] 
        repo_name = repo_namepart1+'/'+repo_namepart2
        
        if 'GET' == method and 'blob' in uri:
            # uri format: v2/<username>/<repo name>/[blobs/uploads | manifests]/<manifest or layer id>
    #        timestamp = datetime.datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
            print "layer_id: "+layer_id_or_manifest_id
            layerTOtimedic[layer_id_or_manifest_id].append(timestamp)
	    try:
                layerToCcntdic[layer_id_or_manifest_id][1] += 1
	    except:

		layerToCcntdic[layer_id_or_manifest_id] = [size, 1]
                #layerToCcntdic[layer_id_or_manifest_id][1] = size
	    
	    try:
		repoToCcntdic[repo_name] += 1
	    except:
                repoToCcntdic[repo_name] = 0

	    try:
		usrToCcntdic[clientAddr] += 1
	    except:
                usrToCcntdic[clientAddr] = 0
            
        if 'GET' == method and 'manifest' in uri:    
            usrrepokey = clientAddr+':'+repo_name
            usrrepoTOtimedic[usrrepokey].append(timestamp)
            usrTOtimedic[clientAddr].append(timestamp)
            
            try:
                lst = usrTorepocntdic[clientAddr]
                find = 0
                for tup in lst:
                    if repo_name == tup[0]:
                        x = tup[1]
                        x += 1
                        lst.remove(tup)
                        lst.append((tup[0], x))
                        find = 1
                if 0 == find:
                   usrTorepocntdic[clientAddr].append((repo_name, 1)) 
            except:
                usrTorepocntdic[clientAddr].append((repo_name, 1)) 
                        
    with open(os.path.join(input_dir, fname + '-layer_access_timestamp.json'), 'w') as fp:
        json.dump(layerTOtimedic, fp)
    with open(os.path.join(input_dir, fname + '-usrrepo_access_timestamp.json'), 'w') as fp:
        json.dump(usrrepoTOtimedic, fp)
    with open(os.path.join(input_dir, fname + '-usr_access_timestamp.json'), 'w') as fp:
        json.dump(usrTOtimedic, fp)
        
        
    with open(os.path.join(input_dir, fname + '-layer_access_cnt.json'), 'w') as fp:
        json.dump(layerToCcntdic, fp)
    with open(os.path.join(input_dir, fname + '-repo_access_cnt.json'), 'w') as fp:
        json.dump(repoToCcntdic, fp)
    with open(os.path.join(input_dir, fname + '-usr_access_cnt.json'), 'w') as fp:
        json.dump(usrToCcntdic, fp)
    with open(os.path.join(input_dir, fname + '-usr_access_repo_cnt.json'), 'w') as fp:
        json.dump(usrTorepocntdic, fp)


def analyze_repo_reqs(total_trace):
#     usrTOrepoTOlayerdic = defaultdict(list) # repoTOlayerdic
    repoTOlayerdic = defaultdict(list)
#     usrTOrepodic = defaultdict(list) # repoTOlayerdic
    fname = os.path.basename(total_trace)
    
    print("the output file is %s", os.path.join(input_dir, fname + '-repo2layersdic-withsize.json'))
    
    with open(total_trace, 'r') as f:
        blob = json.load(f)

    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name

        if 'blob' in uri: # only layers
            layer_id = uri.rsplit('/', 1)[1]
#             timestamp = r['timestamp']
    #        timestamp = datetime.datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
            method = r['http.request.method']
            size = r['http.response.written']
            
            if 'GET' != method:
                continue

            print "layer_id: " + layer_id
            print "repo_name: " + repo_name
#             print "usrname: "+usrname

#             if repo_name in repoTOlayerdic.keys():
#                 if layer_id not in repoTOlayerdic[repo_name]:
#                     repoTOlayerdic[repo_name].append(layer_id)
#             else:
#                 repoTOlayerdic[repo_name].append(layer_id)
            found = False
            
            try:
                lst = repoTOlayerdic[repo_name]
                for l, _ in lst:
                    if layer_id == l:
                        found = True
                if not found:
                    repoTOlayerdic[repo_name].append((layer_id, size))
            except Exception as e:
                print "repo has not this layer before or first met his repo"
                repoTOlayerdic[repo_name].append((layer_id, size))

#             try:
#                 lst = usrTOrepodic[usrname]
#                 if repo_name not in lst:
#                     usrTOrepodic[usrname].append(repo_name)
#             except Exception as e:
#                 print "usrname has not this repo before"
#                 usrTOrepodic[usrname].append(repo_name)
#             if layer_id

    #         if layer_id in layerTOtimedic.keys():
            #layerTOtimedic[layer_id].append((method, timestamp))
#             repoTOlayerdic[repo_name].append(layer_id)

#     for repo in repoTOlayerdic.keys():
#         jsondata = {
#             ''
#         }

#     for usr in usrTOrepodic.keys():
#         for repo in usrTOrepodic[usr]:
#             usrTOrepoTOlayerdic[usr].append({repo:repoTOlayerdic[repo]})
# 
#     for usr in usrTOrepodic.keys():
#         jsondata = {
#             'usr': usr,
#             'repos': usrTOrepoTOlayerdic[usr]
# 
#         }

    with open(os.path.join(input_dir, fname + '-repo2layersdic-withsize.json'), 'w') as fp:
        json.dump(repoTOlayerdic, fp)


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
        #print request
        organized[clientAddr].append(request)
    return organized


##############################
#Keren 8/6
debug = True
def smartclusterClientReqs(total_trace):
    organized = defaultdict(list)
    fname = os.path.basename(total_trace)
    print "the output file would be: " + input_dir + fname + '-smart_sorted_reqs_repo_client.lst'
    if debug:
        print 'debugging enabled...'
        abn_get = 0
        abn_put = 0
        abn_clustering = 0
        abn_clusters = {}
        total_put = 0
        total_get = 0
        buff = []
    organized = clusterUserreqs(total_trace)

    img_req_group = []
    #for all the requests from each client
    for cli, reqs in organized.items():
        cli_img_req_group = [[]]
        prev = cli_img_req_group[-1]
        #prev_repo = ''
        cur = []
        #for each request
        for req in reqs:
            uri = req['uri']
            layer_or_manifest_id = uri.rsplit('/', 1)[1]
            parts = uri.split('/')
            repo = parts[1] + '/' + parts[2]
	    #if debug:
            #    print req
            #params:repo, method(get/put), type (Manifest/layer)
            #fixed: client
            #rules: repo change = new cluster
            #       get cluster: get m, get l, get l...
            #       put:         put l, put l...put m
            # so: a cluster is a set of requests confirming the get/put pattern
            # and are all on the same repo; a cluster is supposed to be a single get/put image request
            if True: #prev_repo == repo:
                #still the same person working with the same repo
                
                if req['method'] == 'GET':
                    '''if len(prev) != 0:
                        tmp = prev[0]['uri'].split('/')
                        prepo = tmp[1] + '/' + tmp[2]
                        if prepo != repo:
                            abn_clustering += 1
                            abn_clusters[prev[0]['delay']] = prev'''
                    # if we see a get request
                    print 'GET: '+'uri'
                    if 'blobs' in uri:
                        # continue on the old get request
                        print 'GET layer'
                        prev.append(req)
                    else:
                        # start of new cluster
                        print 'GET manifest'
                        cur = []
                        cur.append(req)
                        cli_img_req_group.append(cur)
                        prev = cli_img_req_group[-1]
                    total_get += 1
                    if debug and prev[0]['method'] != 'GET':
                            abn_get += 1
                    if len(prev) > 1:
                        tmp = prev[0]['uri'].split('/')
                        prepo = tmp[1] + '/' + tmp[2]
                        if prepo != repo:
                            abn_clustering += 1
                            abn_clusters[prev[0]['delay']] = prev
                '''else:
                    #if we see a put request
                    print 'PUT: '+'uri'
                    if 'blobs' in uri:
                        print 'PUT layer'
                        if len(prev) > 0 and prev[0]['method'] != 'PUT':
                            print 'new put cluster; should only appear after get cluster'
                            cur = []
                            cur.append(req)
                            cli_img_req_group.append(cur)
                            prev = cli_img_req_group[-1]
                        else:
                            prev.append(req)
                    elif 'manifests' in uri:
                        print 'PUT manifest'
                        prev.append(req)
                        cur = []
                        cli_img_req_group.append(cur)
                        if debug and (prev[0]['method'] != 'PUT'):
                            abn_put += 1
                        prev = cli_img_req_group[-1]
                    total_put += 1'''
            '''else:
                print 'new repo'
                #started working with a new layer
                prev_repo = repo
                #start a new record regardless of specific request type
                cur = []
                cur.append(req)
                cli_img_req_group.append(cur)
                prev = cli_img_req_group[-1]'''
#         cli_img_req_group = cli_img_pull_group + cli_img_push_group
	cli_img_req_group_new = [x for x in cli_img_req_group if x and len(x) > 1]
	print cli_img_req_group_new
        #cli_img_req_group.sort(key= lambda x: x[0]['delay'])
        img_req_group += cli_img_req_group_new
    img_req_group.sort(key= lambda x: x[0]['delay'])
#     return img_req_group
    with open(input_dir + fname + '-smart_sorted_reqs_repo_client.lst', 'w') as fp:
        json.dump(img_req_group, fp)

    if debug:
       print 'abnormal puts = ' + str(abn_put) + '; abnormal gets = ' + str(abn_get) + '... total puts = ' + str(total_put) + '; total gets = ' + str(total_get)
       print 'abnormal requests: ' + str(abn_clustering) + ', abnormal clusters: ' + str(len(abn_clusters))
    with open('abnormities.txt', 'w') as fp:
        json.dump(abn_clusters, fp)

##############################

def clusterClientReqs(total_trace):
    organized = defaultdict(list)
    fname = os.path.basename(total_trace)
    print "the output file would be: " + input_dir + fname + '-sorted_reqs_repo_client.lst'

    organized = clusterUserreqs(total_trace)

    img_req_group = []
    for cli, reqs in organized.items():
        cli_img_req_group = [[]]
        prev = cli_img_req_group[-1]
        cur = []
        #print "cli: "
        #print cli
        #print "reqs"
        #print reqs
        #return
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
    with open(input_dir + fname + '-sorted_reqs_repo_client.lst', 'w') as fp:
        json.dump(img_req_group, fp)
#     return organized


def clusterClientReqForClients(total_trace):
    organized = defaultdict(list)
    fname = os.path.basename(total_trace)
    print "the output file would be: " + input_dir + fname + '-sorted_reqs_repo_clientForclients.json'

    organized = clusterUserreqs(total_trace)
    img_req_group = defaultdict(list)
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
        img_req_group[cli]= cli_img_req_group_new
    with open(input_dir + fname + '-sorted_reqs_repo_clientForclients.json', 'w') as fp:
        json.dump(img_req_group, fp)


def clusterClientRepoPull(total_trace):
    fname = os.path.basename(total_trace)
    print "the output file would be: " + input_dir + fname +'_clusterClientRepoPull.json'
    with open(input_dir + fname + '-sorted_reqs_repo_clientForclients.json', 'r') as fp:
        blob = json.load(fp)

    client_repo_dict = defaultdict(list)

    f = open(input_dir + fname + '-_clusterClientRepoPull.lst', 'w')

    for client, rlst in blob.items():
        print client
        print rlst
        print 'end...'
        exit(0)
        repo_state_dict = {}
        if 0 == len(rlst):
            print "empty reqs"

        for r in rlst:
            uri = r[0]['uri']
#         layer_or_manifest_id = uri.rsplit('/', 1)[1]

            if (r[0]['method'] != 'GET') or ('manifest' not in r[0]['uri']):
                print "a wrong request"
                print r
                continue

            parts = uri.split('/')
            repo = parts[1] + '/' + parts[2]
            #key = client address : reponame
            layer_or_manifest_id = uri.rsplit('/', 1)[1]
            key = r[0]['clientAddr'] + ':' + repo

            if 1 == len(r):
                print "empty get manifest request"
                if key in repo_state_dict.keys():
#                    repo_state_dict[key][0] += 1
#                    repo_state_dict[key][2] += 1

                    repo_state_dict[key] = (repo_state_dict[key][0]+1, repo_state_dict[key][1], repo_state_dict[key][2]+1, repo_state_dict[key][3])
                else:
                    repo_state_dict[key] = (1,0,1,[]) # empty get count, repull cnt, total pull cnt
                continue

            llst = []
            for l in r[1:]:
                uri = l['uri']
                lid = layer_or_manifest_id = uri.rsplit('/', 1)[1]
                llst.append(lid)

            if key in repo_state_dict.keys():
                prev_lst = repo_state_dict[key][3]
                repulled_lst = list(set(prev_lst) & set(llst))
                if len(repulled_lst) >= 0.5*len(prev_lst) or len(repulled_lst) >= 0.5*len(llst):
                    repo_state_dict[key] = (repo_state_dict[key][0], repo_state_dict[key][1] + 1, repo_state_dict[key][2] + 1, list(set(prev_lst) | set(llst)))
                else:
                    repo_state_dict[key] = (repo_state_dict[key][0], repo_state_dict[key][1], repo_state_dict[key][2] + 1, list(set(prev_lst) | set(llst)))
                #repo_state_dict[key][2] += 1

                #repo_state_dict[key][3] = list(set(prev_lst) | set(llst))
            else:
                repo_state_dict[key] = (0,0,1,llst) # empty get count, repull cnt, partial pull cnt

        client_repo_dict[client].append(repo_state_dict)

        print client
        print repo_state_dict
        for key in repo_state_dict.keys():
            f.write(str(repo_state_dict[key][0])+'\t'+str(repo_state_dict[key][1])+'\t'+str(repo_state_dict[key][2])+'\t\n')

    with open(input_dir + fname +'_clusterClientRepoPull.json', 'w') as fp:
        json.dump(client_repo_dict, fp)

    f.close()


def repullReqsCal(total_trace):
    fname = os.path.basename(total_trace)
    clientTOlayerMap = SqliteDict(input_dir+'/usrRepulls/'+ fname +'my_repulldb.sqlite', autocommit=True)
    totallayer_cnt = 0
    repulledlayer_cnt = 0
    totallayer_ls = 0
    repulledlayer_ls = 0
    clientrepulllayers_ls = 0
    totalclientrepullayers_ls = 0
    
    f = open(input_dir +'usrRepulls/repullClientratiolst/' + fname + '-layers_repulllayers.lst', 'w')
    fclient = open(input_dir +'usrRepulls/repullClientratiolst/' + fname + '-layers_repulllayers_cnt_client.lst', 'w')

    for cli, lst in clientTOlayerMap.iteritems():
        clientrepulllayers_ls = 0
        totalclientrepullayers_ls = 0
        for tup in lst:
            if 0 == tup[1]:
                totallayer_cnt += 1
            else:
                totallayer_cnt += tup[1]
            if tup[1]:
                repulledlayer_cnt += tup[1]
                clientrepulllayers_ls += 1
                repulledlayer_ls += 1
            totallayer_ls += 1
            totalclientrepullayers_ls += 1
	    f.write(str(tup[1])+'\t\n')
        fclient.write(str(clientrepulllayers_ls)+'\t'+str(totalclientrepullayers_ls)+'\t\n')    
    print "totallayer_reqs cnt:    " + str(totallayer_cnt)
    print "repulledlayer_reqs cnt:   " + str(repulledlayer_cnt)
    print "ratio:  " + str(1.0*repulledlayer_cnt/totallayer_cnt)

    print "totallayer_layers cnt:    " + str(totallayer_ls)
    print "repulledlayer_layerss cnt:   " + str(repulledlayer_ls)
    print "ratio:  " + str(1.0*repulledlayer_ls/totallayer_ls)

    clientTOlayerMap.close()
    fclient.close()
    f.close()

# repull layer cnt / total layer pulls
def repullReqUsr(total_trace):
    fname = os.path.basename(total_trace)
    clientTOlayerMap = SqliteDict(input_dir+'/usrRepulls/'+ fname +'my_dba.sqlite', autocommit=True)

    f = open(input_dir +'usrRepulls/repullClientratiolst/' + fname + '-layers_repulllayers_client.lst', 'w')
    for cli, lst in clientTOlayerMap.iteritems():
        usrlayer_cnt = 0
        repulledlayer_cnt = 0
        for tup in lst:
            if 0 == tup[1]:
                usrlayer_cnt += 1
            else:
                usrlayer_cnt += tup[1]
            if tup[1]:
                repulledlayer_cnt += tup[1]
        f.write(str(usrlayer_cnt)+'\t'+str(repulledlayer_cnt)+'\t\n')
    print "totallayer_cnt:    " + str(usrlayer_cnt)
    print "repulledlayer_cnt:   " + str(repulledlayer_cnt)
    print "ratio:  " + str(1.0*repulledlayer_cnt/usrlayer_cnt)
    clientTOlayerMap.close()
    f.close()


def getGetManfiests(total_trace):
    fname = os.path.basename(total_trace)
    print "the output file would be: " + input_dir + fname +'_getgetmanifests_nl.json'
    with open(input_dir + fname + '-sorted_reqs_repo_client.lst', 'r') as fp:
        blob = json.load(fp)

    client_repo_dict = defaultdict(list)

    for r in blob:
        uri = r[0]['uri']
#         layer_or_manifest_id = uri.rsplit('/', 1)[1]
        parts = uri.split('/')
        repo = parts[1] + '/' + parts[2]
        #key = client address : reponame

        if (r[0]['method'] != 'GET') or ('manifest' not in r[0]['uri']):
            print "a wrong requests"
            print r
            continue

        key = r[0]['clientAddr'] + ':' + repo

        tup = (r[0]['delay'], len(r) - 1)
        print key
        print tup
        client_repo_dict[key].append(tup)

#         try:
#             lst = client_repo_dict[key]
#             client_repo_dict[key].append(r)
#         except Exception as e:
#             client_repo_dict[key].append(r)
    with open(input_dir + fname +'_getgetmanifests.json', 'w') as fp:
        json.dump(client_repo_dict, fp)

    GetM_l = [] # duration between two subsequent get manifest with layers for same client and same repo
    GetM_ln = [] # duration between two subsequent get manifests, first with layers, later without layers
    nothing = 0
    pulls  = 0
    for key, lst in client_repo_dict.items():
	pulls += 1
        if (len(lst) < 2) and (0 == lst[0][1]):
            nothing += 1
            print "this client doesn't pull anything from this repo at all"
	if len(lst) < 2:
            continue

        first = False
        prev = 0
        for tup in lst:
            if tup[1] != 0:
                if first: # prev get manifest with layers, and this also has layer
                    t = datetime.datetime.strptime(tup[0], '%Y-%m-%dT%H:%M:%S.%fZ')
                    delta = t - prev
                    delta = delta.total_seconds()
                    GetM_l.append(delta)
                else:
                    prev = datetime.datetime.strptime(tup[0], '%Y-%m-%dT%H:%M:%S.%fZ')
		    first = True
            else:
                if first: # prev get manifest layers, and this don't has layer
                    t = datetime.datetime.strptime(tup[0], '%Y-%m-%dT%H:%M:%S.%fZ')
                    delta = t - prev
                    delta = delta.total_seconds()
                    GetM_ln.append(delta)
#                 else: # prev dont have layers and so as this one
#                     prev = datetime.datetime.strptime(lst[0][0], '%Y-%m-%dT%H:%M:%S.%fZ')
#                     pass
#         print rintervals_GET_ML
#         intervals_GET_MLs.append(rintervals_GET_ML)
#         lst.extend(rintervals_GET_ML)
    print "num of clients repo reqs do not pull anything: " + str(nothing*1.0/pulls)
    print "avg interval between a get manifest with layers and a get manifest with layers:" + str(sum(GetM_l)*1.0 / len(GetM_l))
    print "number: "+str(len(GetM_l))
    print "midian is:  "+ str(statistics.median(GetM_l))

    print "all intervals:====>"
    print "mean: "+ str(numpy.mean(GetM_l))
    print "10 percentile: "+str(numpy.percentile(GetM_l, 10))
    print "25 percentile: "+str(numpy.percentile(GetM_l, 25))
    print "39 percentile: "+str(numpy.percentile(GetM_l, 39))
    print "max: "+str(numpy.amax(GetM_l))
    print "min: "+str(numpy.amin(GetM_l))

    print "avg interval between a get manifest with layers and a get manifest without layers:" + str(sum(GetM_ln)*1.0 / len(GetM_ln))
    print "number: "+str(len(GetM_ln))
    print "midian is:  "+ str(statistics.median(GetM_ln))

    print "all intervals:====>"
    print "mean: "+ str(numpy.mean(GetM_ln))
    print "1 percentile: "+str(numpy.percentile(GetM_ln, 1))
    print "25 percentile: "+str(numpy.percentile(GetM_ln, 25))
    print "39 percentile: "+str(numpy.percentile(GetM_ln, 39))
    print "max: "+str(numpy.amax(GetM_ln))
    print "min: "+str(numpy.amin(GetM_ln))


    with open(input_dir + fname +'_getgetmanifests_GetM_l.json', 'w') as fp:
        json.dump(GetM_l, fp)

    with open(input_dir + fname +'_getgetmanifests_GetM_ln.json', 'w') as fp:
        json.dump(GetM_ln, fp)


#
def durationmanifestblobs(total_trace):
    with open(total_trace + '-smart_sorted_reqs_repo_client.lst', 'r') as fp:
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

    with open(total_trace + 'intervals_client_GET_MLs-no_batch.lst', 'w') as fp:
        json.dump(intervals_GET_MLs, fp)
    with open(total_trace +'intervals_GET_MLs-no_batch.lst', 'w') as fp:
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
    print "mean: "+ str(numpy.mean(all_intervals))
    print "50 percentile: "+str(numpy.percentile(all_intervals, 50))
    print "75 percentile: "+str(numpy.percentile(all_intervals, 75))
    print "99 percentile: "+str(numpy.percentile(all_intervals, 99))
    print "max: "+str(numpy.amax(all_intervals))
    print "min: "+str(numpy.amin(all_intervals))

    with open('intervals_client_GET_MLs.lst', 'r') as fp:
        data = json.load(fp)

    client_img_pull_intervals = numpy.array(data, dtype=object)
    out = numpy_fillna(client_img_pull_intervals)
    len = out.shape[1]
    num_arrays = 0
    if len % 3 == 0:
        num_arrays = len/3
    else:
        num_arrays = len/3 + 1
    array_lst = numpy.array_split(out, num_arrays, 1)
    print num_arrays
    print array_lst
    i = 1
    outputstat = []
    for ar in array_lst:
#         lst = ar.tolist()
#         ar_lst = numpy.array(lst)
        ar_lst_nozeros = numpy.ma.masked_equal(ar, 0).compressed()
#         tmp = []
        print "batch intervals:====> "+str(i)+" batch"
        print "mean: "+ str(numpy.mean(ar_lst_nozeros))
        print "50 percentile: "+str(numpy.percentile(ar_lst_nozeros, 50))
        print "75 percentile: "+str(numpy.percentile(ar_lst_nozeros, 75))
        print "99 percentile: "+str(numpy.percentile(ar_lst_nozeros, 99))
        print "max: "+str(numpy.amax(ar_lst_nozeros))
        print "min: "+str(numpy.amin(ar_lst_nozeros))
        outputstat.append([numpy.mean(ar_lst_nozeros), numpy.percentile(ar_lst_nozeros, 50), numpy.percentile(ar_lst_nozeros, 75), numpy.percentile(ar_lst_nozeros, 99), numpy.amax(ar_lst_nozeros), numpy.amin(ar_lst_nozeros)])
        i += 1
    with open('batch_intervalstat_mean_50_75_99_max_min.lst', 'w') as fp:
        json.dump(outputstat, fp)


def RepoLayerMap(total_trace):
    with open(total_trace, 'r') as fp:
        blob = json.load(fp)

    repoTOlayerMap = defaultdict(list)
    method = r['http.request.method']

    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name

        if ('blobs' in uri) and ('GET' == method):
            layer_id = uri.rsplit('/', 1)[1]

            print "layer_id: "+layer_id
            print "repo_name: "+repo_name

            find = False
            try:
                lst = repoTOlayerMap[repo_name]
                if layer_id not in lst:
#                 for tup in lst:
#                     if tup[0] == layer_id:
#                         find = True
#                         tup[1] += 1
# #                         newtup = (layer_id, tup[1]+1)
# #                         clientTOlayerMap[clientAddr].append(newtup)
#                         print clientAddr + ', ' + layer_id + ', ' + str(tup[1]+1)
#                         break
#
#                 if not find:
                    print "repo_name has not this layer before"
                    repoTOlayerMap[repo_name].append(layer_id)
                    print  repo_name + ', ' + layer_id
            except Exception as e:
                print "repo_name has not this layer before"
                repoTOlayerMap[repo_name].append(layer_id)
                print  repo_name + ', ' + layer_id

    with open('repoTOlayerMap.json', 'w') as fp:
        json.dump(repoTOlayerMap, fp)

#     for i in range(0, len, 3):
#         batch = out[:,1:len:3]
####


def mergeOrderedArr(first, second):
    in_first = set(first)
    in_second = set(second)

    print in_first
    print in_second

    in_second_but_not_in_first = in_second - in_first

    result = first_list + list(in_second_but_not_in_first)
    print result
    return result


def orderedRepoLayerMap():
    with open('client_get_layers_reqs', 'r') as fp:
        blob = json.load(fp)

#     with open('repoTOlayerMap.json', 'r') as fp:
#         repoTOlayerMap = json.load(fp)

    repoTOlayerMap = defaultdict(list)
    method = r['http.request.method']

    for r in blob:
        uri = r['http.request.uri']
        usrname = uri.split('/')[1]
        repo_name = uri.split('/')[2]
        repo_name = usrname+'/'+repo_name

        if ('blobs' in uri) and ('GET' == method):
            layer_id = uri.rsplit('/', 1)[1]

            print "layer_id: "+layer_id
            print "repo_name: "+repo_name

            find = False
            try:
                lst = repoTOlayerMap[repo_name]
                if layer_id not in lst:
#                 for tup in lst:
#                     if tup[0] == layer_id:
#                         find = True
#                         tup[1] += 1
# #                         newtup = (layer_id, tup[1]+1)
# #                         clientTOlayerMap[clientAddr].append(newtup)
#                         print clientAddr + ', ' + layer_id + ', ' + str(tup[1]+1)
#                         break
#
#                 if not find:
                    print "repo_name has not this layer before"
                    repoTOlayerMap[repo_name].append(layer_id)
                    print  repo_name + ', ' + layer_id
            except Exception as e:
                print "repo_name has not this layer before"
                repoTOlayerMap[repo_name].append(layer_id)
                print  repo_name + ', ' + layer_id

    with open('repoTOlayerMap.json', 'w') as fp:
        json.dump(repoTOlayerMap, fp)


def storeGetreqs(total_trace):
    with open(total_trace, 'r') as fp:
        blob = json.load(fp)

    print "finished loading"
    fname = os.path.basename(total_trace)
    print "the output file would be : "+ input_dir + fname + '-client_get_layers_reqs.json'

    req = []
    for r in blob:
        uri = r['http.request.uri']

        clientAddr = r['http.request.remoteaddr']
        method = r['http.request.method']

        if ('blobs' in uri) and ('GET' == method):
            layer_id = uri.rsplit('/', 1)[1]

            print "layer_id: "+layer_id
            u = {
                "clientAddr" : clientAddr,
                "layer_id": layer_id,
            }
            req.append(u)
    with open(input_dir + fname + '-client_get_layers_reqs.json', 'w') as fp:
        json.dump(req, fp)

####
#killed by memory, too big
####
def repullLayers(total_trace):
    fname = os.path.basename(total_trace)
    print "the output sqlite db would be: "+'./'+ fname +'my_dba.sqlite'
    with open(input_dir + fname + '-client_get_layers_reqs.json', 'r') as fp:
        blob = json.load(fp)

#     clientTOlayerMap = defaultdict(list)
#     clientTOlayerMap_1 = defaultdict(list)
    clientTOlayerMap = SqliteDict('./'+ fname +'my_dba.sqlite', autocommit=True)

    repulledlayer_cnt = 0
    totallayer_cnt = 0
    debug_cnt = 0
    for r in blob:
        clientAddr = r['clientAddr']
        layer_id = r['layer_id']
        debug_cnt += 1
        if debug_cnt % 10000 == 0:
            print "debug_cnt: "+str(debug_cnt)
        print "layer_id: "+layer_id

        find = False
        try:
            lst = clientTOlayerMap[clientAddr]
            #print "after try: lst =>"
            #print lst
            for tup in lst:
		#print "tup loop ====>"
		#print tup
		#print tup[0]
                if tup[0] == layer_id:
		    #print "find a same layer_id"
                    find = True
		    x = tup[1]
		    x += 1
		    lst.remove(tup)
		    lst.append((layer_id, x))
                    #tup[1] = x + 1

#                         newtup = (layer_id, tup[1]+1)
		    #print "tup[1]:"
		    #print tup[1]
		    #print "x: "
		    #print x
                    clientTOlayerMap[clientAddr] = lst
                    #print "after try: add repull"
                    #print lst
                    print clientAddr + ', ' + layer_id + ', ' + str(x)
                    break

            if not find:
#                 print "usrname has not this layer before"
                lst.append((layer_id, 0))
                clientTOlayerMap[clientAddr] = lst
		#print "after try: not find: lst ==>"
                #print lst
                print  clientAddr + ', ' + layer_id + ', ' + str(0)
        except Exception as e:
#             print "usrname has not this layer before"
            lst = []
            lst.append((layer_id, 0))
            clientTOlayerMap[clientAddr] = lst
            #print "except: ===>"
            #print lst
            print  clientAddr + ', ' + layer_id + ', ' + str(0)
#                 print  clientAddr + ', ' + layer_id + ', ' + str(0)

    for cli, lst in clientTOlayerMap.iteritems():
        for tup in lst:
            totallayer_cnt += 1
            if tup[1]:
                repulledlayer_cnt += 1

    print "totallayer_cnt:    " + str(totallayer_cnt)
    print "repulledlayer_cnt:   " + str(repulledlayer_cnt)
    print "ratio:  " + str(1.0*repulledlayer_cnt/totallayer_cnt)
    clientTOlayerMap.close()
#     with open('client_to_layer_map.json', 'w') as fp:
#         json.dump(clientTOlayerMap, fp)


def main():

    parser = ArgumentParser(description='Trace Player, allows for anonymized traces to be replayed to a registry, or for caching and prefecting simulations.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'Input trace file basename in the input_dir, trace_dir is in analysis.py as global variable, hardcoded')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, help= 'Command.')

    args = parser.parse_args()

    trace_file = input_dir + args.input
    trace_dir = input_dir + args.input
    
    print "input trace file: " + trace_file

    if args.command == 'get':
        print "input trace dir: " + trace_dir
        get_requests(trace_dir)
    elif args.command == 'Alayer':
#         print "wrong cmd!"
        analyze_requests(trace_file)
    elif args.command == 'reusetime':
        analyze_reusetime(trace_file)
    elif args.command == 'repo2layermap':
        analyze_repo_reqs(trace_file)
    elif args.command == 'repolayer':
        analyze_usr_repolifetime()
    elif args.command == 'clusteruserreqs':
        clusterClientReqs(trace_file)
    elif args.command == 'newclusteruserreqs':
        smartclusterClientReqs(trace_file)
    elif args.command == 'calintervalgetML':
        durationmanifestblobs(trace_file)
    elif args.command == 'calbatchstats':
        calbatchstats()
    elif args.command == 'repullLayers':
        repullLayers(trace_file)
    elif args.command == 'storeGetreqs':
        storeGetreqs(trace_file)
    elif args.command == 'getGetManfiests':
        getGetManfiests(trace_file)
    elif args.command == 'repullReqsCal':
        repullReqsCal(trace_file)
    elif args.command == 'clusterClientReqForClients':
        clusterClientReqForClients(trace_file)
    elif args.command == 'clusterClientRepoPull':
        clusterClientRepoPull(trace_file)
    elif args.command == 'repullReqUsr':
        repullReqUsr(trace_file)
    elif args.command == 'getSkewness':
        getSkewness(trace_file)
    else:    
        return


if __name__ == "__main__":
    main()
