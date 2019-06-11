from bottle import route, run, request, static_file, Bottle, response
import hash_ring
import sys, getopt
import yaml
import os
import requests
import json
from argparse import ArgumentParser
from optparse import OptionParser
import time
import socket
import random
import pdb
from multiprocessing import Process, Queue
from dxf import *

import rejson, redis, json
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from uhashring import HashRing
from rediscluster import StrictRedisCluster
startup_nodes = [
             {"host": "192.168.0.170", "port": "7000"}, \
            {"host": "192.168.0.170", "port": "7001"}, \
            {"host": "192.168.0.171", "port": "7000"},  \
            {"host": "192.168.0.171", "port": "7001"}, \
             {"host": "192.168.0.172", "port": "7000"},  \
            {"host": "192.168.0.172", "port": "7001"}, \
            {"host": "192.168.0.174", "port": "7000"}, \
             {"host": "192.168.0.174", "port": "7001"},\
             {"host": "192.168.0.176", "port": "7000"}, \
             {"host": "192.168.0.176", "port": "7001"},\
             {"host": "192.168.0.177", "port": "7000"}, \
             {"host": "192.168.0.177", "port": "7001"},\
             {"host": "192.168.0.178", "port": "7000"}, \
            {"host": "192.168.0.178", "port": "7001"},\
             {"host": "192.168.0.179", "port": "7000"}, \
             {"host": "192.168.0.179", "port": "7001"},\
            {"host": "192.168.0.180", "port": "7000"},\
             {"host": "192.168.0.180", "port": "7001"}]

# {u'SliceSize': 166, u'DurationCP': 0.000751436, u'DurationCMP': 3.7068e-05, u'ServerIp': u'192.168.0.171', u'DurationML': 0.000553802, u'DurationNTT': 3.7041e-05, u'DurationRS': 0.001379347}
restoretime = 'Blob:File:Recipe::RestoreTime::sha256*'
recipe = 'Blob:File:Recipe::sha256*'

rj_dbNoBFRecipe = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)
for key in rj_dbNoBFRecipe.scan_iter(recipe):
    k = key.split('::')[1]
    #print k
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    print "Key: ", key, ", SliceSize: ", bfrecipe['SliceSize'], ", DurationCP: ", bfrecipe['DurationCP'], ", DurationCMP: ", bfrecipe['DurationCMP'], ", DurationML: ", bfrecipe['DurationML'], ", DuraionNTT: ", bfrecipe['DurationNTT'], ", DurationRS: ", bfrecipe['DurationRS']#"Blobigest: ", bfrecipe['BlobDigest'], ", LayerDurationCP: ", bfrecipe['LayerDurationCP'], ", LayerDuraionNTT: ", bfrecipe['LayerDurationNTT'], ", CompressSize: ", bfrecipe['CompressSize']
    if bfrecipe['DurationCMP'] and bfrecipe['DurationDCMP'] and bfrecipe['DurationNTT']:
    	#print bfrecipe
   	newkeystar = 'Blob:File:Recipe::RestoreTime::'+k+'*'
	#print newkeystar
	durationrs = []
	for newkey in rj_dbNoBFRecipe.scan_iter(newkeystar):
	    bfrestaretime = json.loads(rj_dbNoBFRecipe.execute_command('GET', newkey))
	    durationrs.append(bfrestaretime['DurationRS'])
	    maxrs = max(durationrs)
	print(bfrecipe['CompressSize'],  maxrs, bfrecipe['DurationDCMP'], bfrecipe['DurationCMP'], bfrecipe['DurationNTT'])
        #break

#key = "Blob:File:Recipe::sha256:808442aea3fd7583588e24a7f80b5556070e80326f7964cd32b16dd04f2c42de"
#bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
#print bfrecipe

"""
for key in rj_dbNoBFRecipe.scan_iter("Blob:File:Recipe::RestoreTime*"):
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    print(bfrecipe["SliceSize"], bfrecipe["DurationRS"], bfrecipe["DurationCP"], bfrecipe["DurationCMP"], bfrecipe["DurationML"], bfrecipe["DurationNTT"])
"""
