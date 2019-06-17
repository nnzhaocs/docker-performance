import sys
import os
import json
from argparse import ArgumentParser

trace_dir = '/home/nannan/dockerimages/docker-traces/downloaded-traces/data_centers/'

def main():
    total_req_count = 0
    total_lyr_count = 0
    percentage = 0
    req_count = 0
    lyr_hit = 0
    reqs = []
    lyrs = []
    empty_count = 0

    parser = ArgumentParser(description='chop down a trace file into smaller trunks')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'trace file in')
    parser.add_argument('-o', '--output', dest='output', type=str, required=True, help = 'trace file out')
    parser.add_argument('-p', '--percent', dest='prst', type=str, required=True, help = 'first X percent of the file extracted')
    args = parser.parse_args()
    if int(args.prst) < 0 or int(args.prst) > 100:
        print 'invalid percentage'
        exit(-1)

    percentage = int(args.prst)
    print 'reading in input file...'
    with open(trace_dir + args.input, 'r') as fr:
        temp = json.load(fr)
    total_req_count = len(reqs)

    print 'read file successful, now getting unique layers'
    for req in temp:
        method = req['http.request.method']
        uri = req['http.request.uri']
        if (('GET' == method) or ('PUT' == method)) and (('manifest' in uri) or ('blobs' in uri)):
            size = req['http.response.written']
            if  size == 0:
                empty_count += 1
                continue
            reqs.append(req)
            print uri
            layer_id = uri.split('/')[-1]
            if layer_id not in lyrs:
                lyrs.append(layer_id)
    print 'layers got'
    total_lyr_count = len(lyrs)
    
    #print 'read file successful, now getting unique entry counts...'
    total_req_count = len(reqs)

    print 'successfully read in ' + str(total_req_count) +  ' requests'
    print 'successfully read in ' + str(total_lyr_count) +  ' layers'
    print 'now extracting requests to hit ' + str(percentage) + ' percent of layers...'

    length = int(total_lyr_count * percentage / 100)
    results = []
    for i in range (0, 1700): #req in reqs:
        #if length == lyr_hit :
        #    break
        #req_count += 1
        lyr_id = reqs[i]['http.request.uri'].split('/')[-1]
        if lyr_id in results :
            continue
        lyr_hit += 1
        results.append(lyr_id)
    print len(results)
    results.sort()
    print len(set(results))
    print results
    #print 'Extraction complete. It took ' + str(req_count) + ' requests to hit ' + str(lyr_hit) + 'layers'

    #print 'writing out results to specified output file...'
    #with open(trace_dir + args.output, 'w') as fo:
    #        json.dump(results, fo)
 


if __name__ == "__main__":
    main()

