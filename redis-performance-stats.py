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

rj_dbNoBFRecipe = StrictRedisCluster(startup_nodes=startup_nodes, decode_responses=True)

for key in rj_dbNoBFRecipe.scan_iter("Blob:File:Recipe::RestoreTime*"):
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    print(bfrecipe["SliceSize"], bfrecipe["DurationRS"], bfrecipe["DurationCP"], bfrecipe["DurationCMP"], bfrecipe["DurationML"], bfrecipe["DurationNTT"])

