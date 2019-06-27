import sys
import os
import json
from argparse import ArgumentParser

realblobtrace_dir = "/home/nannan/testing/realblobtraces/"
server_file = os.getcwd() + "/run/remotehostthors.txt"

def chop(traces, servers):
    print 'the chopping has started...'
    trunk_size = len(traces) / len(servers) / 5
    print 'each trunk will have size of ' + str(trunk_size)
    # chopping original data into chunks;
    i = 0
    lister = range(len(traces))
    for server in servers:
       #for i in range(1, 5):
       print 'chopping for ' + server
       for j in range(1, 5):
           #print lister[i:i+trunk_size]
           chunk = traces[i:i+trunk_size]
           with open(realblobtrace_dir+server+str(j)+'.json', 'w') as f:
               json.dump(chunk, f)
           i += trunk_size
           #chunk = traces[i : i + trunk_size]
def main():
    global realblobtrace_dir
    global server_file
    realblobtrace_file = None

    parser = ArgumentParser(description='N/A')
    parser.add_argument('-rbt', '--rbt', dest='rbt', type=str, required=False, 
                        help = 'read blob trace file to be divided')
    parser.add_argument('-s', '--server', dest='server', type=str, required=False, 
                        help = 'server name file.')
    args = parser.parse_args()
    if args.rbt != None:
        realblobtrace_dir += args.rbt
    else:
        print 'realblob trace file unspecified; trying to use default file'
        files = [f for f in os.listdir(realblobtrace_dir) if os.path.isfile(realblobtrace_dir + f)]
        for f in files:
            if ".json" not in f:
                continue
            realblobtrace_file = realblobtrace_dir + f
            break
        if os.path.isfile(realblobtrace_file) == False:
            print 'cannot locate realblobtrace'
            exit(-1)
    if args.server != None:
        server_file = os.getcwd() + args.server
    else:
        print 'server file unspecified; trying to use default file'

    print 'identifying servers...'
    servers = []
    with open(server_file, 'r') as f:
        lines = f.readlines()
        #lines = [line for line in lines if line]
        un_servers = [x.strip() for x in lines]
        for server in un_servers:
            if server != '':
                servers.append(server)
        print str(len(servers)) + 'servers identified'
        print servers
        if len(servers) == 0:
            print 'missing server info'
            exit(-1) 
    
    traces = []
    with open(realblobtrace_file, 'r') as f:
        #lines = f.readlines()
        traces = json.load(f)#[x.strip() for x in lines]
        print 'file readed: ' + realblobtrace_file
        print 'traces identified: ' + str(len(traces))
    chop(traces, servers)

if __name__ == "__main__":
    main()
