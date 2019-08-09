import sys
import os
import json 

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

    getlayerlatency = 0
    gettotallayer = 0
    getlayerlatencies = []

    getmanifestlatency = 0
    gettotalmanifest = 0
    getmanifestlatencies = []

    putlayerlatency = 0
    puttotallayer = 0
    putlayerlatencies = []

    putmanifestlatency = 0
    puttotalmanifest = 0
    putmanifestlatencies = []

    warmuplayerlatency = 0
    warmuptotallayer = 0
    warmuplayerlatencies = []

    warmupmanifestlatency = 0
    warmuptotalmanifest = 0 
    warmupmanifestlatencies = []   

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
        except Exception as e:
            if "failed" in r['onTime']:
                total -= 1
                failed += 1
                continue
            if r['time'] + r['duration'] > endtime:
                endtime = r['time'] + r['duration']
            latency += r['duration']
            data += r['size']
        
        if r['type'] == 'LAYER':
            getlayerlatency += r['duration']
            gettotallayer += 1
            getlayerlatencies.append((r['duration'], r['size']))
            
        if r['type'] == 'MANIFEST':
            getmanifestlatency += r['duration']
            gettotalmanifest += 1
            getmanifestlatencies.append((r['duration'], r['size']))
            
        if r['type'] == 'PUSHLAYER':
            putlayerlatency += r['duration']
            puttotallayer += 1
            putlayerlatencies.append((r['duration'], r['size']))
            
        if r['type'] == 'PUSHMANIFEST':
            putmanifestlatency += r['duration']
            puttotalmanifest += 1
            putmanifestlatencies.append((r['duration'], r['size']))
            
        if r['type'] == 'warmuplayer':
            warmuplayerlatency += r['duration']
            warmuptotallayer += 1
            warmuplayerlatencies.append((r['duration'], r['size']))
            
        if r['type'] == 'warmupmanifest':
            warmupmanifestlatency += r['duration']
            warmuptotalmanifest += 1
            warmupmanifestlatencies.append((r['duration'], r['size']))
                
    duration = endtime - startTime
    print 'Statistics'
    print 'Successful Requests: ' + str(total)
    print 'Failed Requests: ' + str(failed)
    print 'Duration: ' + str(duration)
    print 'Data Transfered: ' + str(data) + ' bytes'
    print 'Average Latency: ' + str(latency / total)
    print 'Throughput: ' + str(1.*total / duration) + ' requests/second'
    print 'Total GET layer: ' + str(gettotallayer)
    print 'Total GET manifest: ' + str(gettotalmanifest)
    print 'Total PUT layer: ' + str(puttotallayer)
    print 'Total PUT Manifest: ' + str(puttotalmanifest)
    print 'Total WAMRUP layer: ' + str(warmuptotallayer)
    print 'Total WAMRUP manifest: ' + str(warmuptotalmanifest)
    
    if gettotallayer > 0:
        print 'Average get layer latency: ' + str(1.*getlayerlatency/gettotallayer) + ' seconds/request'
    if puttotallayer > 0:
        print 'Average put layer latency: ' + str(1.*putlayerlatency/puttotallayer) + ' seconds/request'
    if warmuptotallayer > 0:
        print 'Average warmup layer latency: ' + str(1.*warmuplayerlatency/warmuptotallayer) + ' seconds/request'

    if gettotalmanifest > 0:
        print 'Average get manifest latency: ' + str(1.*getmanifestlatency/gettotalmanifest) + ' seconds/request'
    if puttotalmanifest > 0:
        print 'Average put manifest latency: ' + str(1.*putmanifestlatency/puttotalmanifest) + ' seconds/request'
    if warmuptotalmanifest > 0:
        print 'Average warmup manifest latency: ' + str(1.*warmupmanifestlatency/warmuptotalmanifest) + ' seconds/request'
    
    with open(os.path.join(results_dir, 'client_getlayerlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in getlayerlatencies))
    with open(os.path.join(results_dir, 'client_getmanifestlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in getmanifestlatencies))
        
    with open(os.path.join(results_dir, 'client_putlayerlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in putlayerlatencies))
    with open(os.path.join(results_dir, 'client_putmanifestlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in putmanifestlatencies))
        
    with open(os.path.join(results_dir, 'client_warmuplayerlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in warmuplayerlatencies))
    with open(os.path.join(results_dir, 'client_warmupmanifestlatencies.lst'), 'w') as fp:
        fp.write('\n'.join('{} {}'.format(x[0],x[1]) for x in warmupmanifestlatencies))

 

def main():
    with open(os.path.join(results_dir, fname), 'r') as fp:
        data = json.load(fp)
    
    stats(data)
   

if __name__ == "__main__":
    main()
