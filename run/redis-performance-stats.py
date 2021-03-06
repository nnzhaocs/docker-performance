import os
import json
from rediscluster import StrictRedisCluster

startup_nodes_thors =[{"host": "192.168.0.214", "port": "7000"},
                {"host": "192.168.0.214", "port": "7001"},
                 {"host": "192.168.0.215", "port": "7000"},
                 {"host": "192.168.0.215", "port": "7001"},
                 {"host": "192.168.0.216", "port": "7000"},
                 {"host": "192.168.0.216", "port": "7001"},
                 {"host": "192.168.0.217", "port": "7000"},
                                                                {"host": "192.168.0.217", "port": "7001"},

                                                                        {"host": "192.168.0.218", "port": "7000"},
                                                                                {"host": "192.168.0.218", "port": "7001"},

                                                                                        {"host": "192.168.0.219", "port": "7000"},
                                                                                                {"host": "192.168.0.219", "port": "7001"},

                                                                                                        {"host": "192.168.0.221", "port": "7000"},
                                                                                                                {"host": "192.168.0.221", "port": "7001"},

                                                                                                                        {"host": "192.168.0.222", "port": "7000"},
                                                                                                                                {"host": "192.168.0.222", "port": "7001"},

                                                                                                                                        {"host": "192.168.0.223", "port": "7000"},
                                                                                                                                                {"host": "192.168.0.223", "port": "7001"}]

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
#             {"host": "192.168.0.178", "port": "7000"}, \
#            {"host": "192.168.0.178", "port": "7001"},\
             {"host": "192.168.0.179", "port": "7000"}, \
             {"host": "192.168.0.179", "port": "7001"},\
            {"host": "192.168.0.180", "port": "7000"},\
             {"host": "192.168.0.180", "port": "7001"}]

layerrecipe = 'Layer:Recipe::sha256:*'
slicerecip = 'Slice:Recipe::*'
f = 'File::*'

ulmap = 'ULMap::*'
rlmap = 'RLMap::*'

rj_dbNoBFRecipe = StrictRedisCluster(startup_nodes=startup_nodes_thors, decode_responses=True)
def setItem():
        key = "hello:world"
        des = {
                "MasterIp": ["192.168.0.22"],
                }
        rj_dbNoBFRecipe.execute_command('SET', key, json.dumps(des))
        return 

def getItem(key):
	value = rj_dbNoBFRecipe.execute_command('GET', key)
	print value

def getItems(k):
	for key in rj_dbNoBFRecipe.scan_iter(k):
	    dgst = key#.split('sha256:')[1]
	    recipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
	    print(dgst, recipe)
	    """	
	    uncompressionsize = recipe['UncompressionSize']
	    sumsize = 0
	    for ip, v in recipe['SliceSizeMap'].items():
		sumsize += v
	    if uncompressionsize-sumsize > 0 and uncompressionsize-sumsize < 1024*1024:
		print(dgst, recipe)
	    	print("diff: %d"%(uncompressionsize-sumsize))
	     """

def main():
	key = '*52299ff7366c1b477b283eea121fa6001a9af556528c2c1dfeabce02de845546'
        #setItem()
        getItems("*623d895b040ce9d")
        #getItems(rlmap)
        #getItems("*23078bcef4d525dfa597ad3f454e6ec16316fd6486fab372ca1a47eeb9066591")
        #getItems("*sha256:978b356c054cb2c8d3bcfab47afc1069edc69de79dad9e519c022adc96650222")
        #getItems("Layer:Recipe::sha256:c6327de0331b9538dc3f56aac344e783f6d1e1b10e509ea93a1b3e41151c3a1a")
        #getItems("Layer:Recipe::*")
	#getItems('*a9cb77c437773f3b')


if __name__ == "__main__":
	main()

#    try:
#	dt = bfrecipe['SliceSizeMap']
#	#print dt
#	s = 0
#	for k, v in dt.items():
#	    s += v
#	    if v >= 100*1024*1024:
#		print dt 
#	    	print s/8/1024/1024
#    except Exception as e:
#	#print "skipping slice recipe"
#	pass

    #print "Key: ", key, ", SliceSize: ", bfrecipe['SliceSize'], ", DurationCP: ", bfrecipe['DurationCP'], ", DurationCMP: ", bfrecipe['DurationCMP'], ", DurationML: ", bfrecipe['DurationML'], ", DuraionNTT: ", bfrecipe['DurationNTT'], ", DurationRS: ", bfrecipe['DurationRS']#"Blobigest: ", bfrecipe['BlobDigest'], ", LayerDurationCP: ", bfrecipe['LayerDurationCP'], ", LayerDuraionNTT: ", bfrecipe['LayerDurationNTT'], ", CompressSize: ", bfrecipe['CompressSize']
#    if bfrecipe['DurationCMP'] and bfrecipe['DurationDCMP'] and bfrecipe['DurationNTT']:
#    	#print bfrecipe
#   	newkeystar = 'Blob:File:Recipe::RestoreTime::'+k+'*'
#	#print newkeystar
#	durationrs = []
#	for newkey in rj_dbNoBFRecipe.scan_iter(newkeystar):
#	    bfrestaretime = json.loads(rj_dbNoBFRecipe.execute_command('GET', newkey))
#	    durationrs.append(bfrestaretime['DurationRS'])
#	    maxrs = max(durationrs)
#	print(bfrecipe['CompressSize'],  maxrs, bfrecipe['DurationDCMP'], bfrecipe['DurationCMP'], bfrecipe['DurationNTT'])
        #break

#key = "Blob:File:Recipe::sha256:808442aea3fd7583588e24a7f80b5556070e80326f7964cd32b16dd04f2c42de"
#bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
#print bfrecipe

"""
for key in rj_dbNoBFRecipe.scan_iter("Blob:File:Recipe::RestoreTime*"):
    bfrecipe = json.loads(rj_dbNoBFRecipe.execute_command('GET', key))
    print(bfrecipe["SliceSize"], bfrecipe["DurationRS"], bfrecipe["DurationCP"], bfrecipe["DurationCMP"], bfrecipe["DurationML"], bfrecipe["DurationNTT"])
"""
