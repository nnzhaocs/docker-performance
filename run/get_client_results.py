import sys
#import socket
import os
from argparse import ArgumentParser
#import requests
import time
import datetime
#import pdb
import random
#import threading
#import multiprocessing
import json 
import yaml
from dxf import *
#from multiprocessing import Process, Queue
#import importlib
#import hash_ring
from collections import defaultdict

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from client import *
from os.path import stat
from uhashring import HashRing


results_dir = "/home/nannan/testing/results/"
fname = "results.json"

#############
# NANNAN: change `onTime` for distributed dedup response
# {'size': size, 'onTime': onTime, 'duration': t}
# {'time': now, 'duration': t, 'onTime': onTime_l}
##############
 
def stats(responses):
    responses.sort(key = lambda x: x['time'])

    endtime = 0
    data = 0
    latency = 0
    total = len(responses)
    onTimes = 0
    failed = 0
    layerlatency = 0
    totallayer = 0
    
    layerlatency = []
    #slicelatency = []
    
    startTime = responses[0]['time']
    for r in responses:
        print r
        try:
            for i in r['onTime']:
                if "failed" in i['onTime']:
                    total -= 1
                    failed += 1
                    break # no need to care the rest partial layer.
            	data += i['size']
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            layerlatency.append((duration, r['size'])
        except Exception as e:
            if "failed" in r['onTime']:
                total -= 1
                failed += 1
                continue
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            data += r['size']
        
        if r['type'] == 'layer':
            layerlatency += r['duration']
            totallayer += 1
            layerlatency.append((duration, r['size']))

            
    duration = endtime - startTime
    print 'Statistics'
    print 'Successful Requests: ' + str(total)
    print 'Failed Requests: ' + str(failed)
    print 'Duration: ' + str(duration)
    print 'Data Transfered: ' + str(data) + ' bytes'
    print 'Average Latency: ' + str(latency / total)
    print 'Throughput: ' + str(1.*total / duration) + ' requests/second'
    if totallayer > 0:
        print 'Average layer latency: ' + str(1.*layerlatency/totallayer) + ' seconds/request'
    
    with open(os.path.join(results_dir, 'client_layer_duration.lst'), 'w') as fp:
	fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in layerlatency)
        #for item in layerlatency:
        #    f.write("%s\n" % str(item))

 
##########annotation by keren
def main():
    with open(os.path.join(results_dir, fname), 'r') as fp:
        data = json.load(fp)
    
    stats(data)
   

if __name__ == "__main__":
    main()
