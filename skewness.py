import sys
import os
import json

with open('/home/nannan/testing/realblobtraces/input_tracefile-realblob.json', 'r') as fp:
	data = json.load(fp)

layeridmap = {}

for req in data:
	uri = req['http.request.uri']
	if 'manifest' in uri:
		continue
	layerid = uri.rsplit('/', 1)[1]
	try:
		x = layeridmap[layerid]
		layeridmap[layerid] += 1
	except:
		layeridmap[layerid] = 1

print layeridmap

with open('syd1000.lst', 'w') as fp:
	for _, val in layeridmap.items():
		fp.write(str(val)+'\t\n')

#sudo python create_yaml_onenode.py -r 1m -t fra -m nodedup -s standard -a 12 -n 1 -c 1 -p 1
"""
awk '$1>=2{s+=$1; c++} END{print s; print c+0}' dal5000.lst
awk '$1==1{s+=$1; c++} END{print s; print c+0}' dal5000.lst
"""
