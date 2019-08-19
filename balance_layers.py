import sys
import os
import random
import copy
import math
from argparse import ArgumentParser

layer_file = ['/home/nannan/dockerimages/layers/hulk1/hulk1_layers_bigger_2g.lst', '/home/nannan/dockerimages/layers/hulk1/hulk1_layers_less_50m.lst']
lyr_name = 'default'

def std_dev(lst):
    avg = 0
    for node in lst:
        avg += node[1]
    avg /= len(lst)
    s = 0
    for node in lst:
        s += (node[1] - avg)**2
    s /= (len(lst) - 1)
    return math.sqrt(s)

def main():

    nodes = [[i, 0, []] for i in range(8)]
    g_nodes = [[i, 0, []] for i in range(8)]
    lyrs = []
    #parser = ArgumentParser(description='chop down a trace file into smaller trunks')
    #parser.add_argument('-i', '--input', dest='input', type=str, required=True, help = 'trace file in')
    #parser.add_argument('-o', '--output', dest='output', type=str, required=True, help = 'trace file out')
    #args = parser.parse_args()
    
    #get layers
    length = random.randint(50, 900)#5k-10w
    #length = 1000
    '''content = []
    print 'reading in layer file...'
    for fn in layer_file:
        print fn
        with open(fn, 'r') as f:
            f_content = f.readlines()
            f_content = [x.strip() for x in f_content]
            print len(f_content) 
            content.extend(f_content)
    #print len(content)
    #get layer sizes
    for lyr in content:'''
    for i in range(length):
        try:
            size = random.randint(0, 5000000)#0 - 500w #os.stat(lyr).st_size
            lyrs.append([lyr_name, size])
        except:
            print 'failed to get size'
    print 'layer length: ' + str(len(lyrs))
    print 'layer size: ' + str(sum([lyr[1] for lyr in lyrs]))
    #get nodes
    print "ignoring actual nodes for now"
    
    #randomly pre put a couple layers into random nodes
    #lyr_names = [lyr[0] for lyr in lyrs]
    dup_count = random.randint(0, 20)
    print dup_count
    for i in range(dup_count):
        node_num = random.randint(-1, 7)
        lyr = random.choice(lyrs)
        nodes[node_num][1] += lyr[1]
        nodes[node_num][2].append(lyr)
        g_nodes[node_num][1] += lyr[1]
        g_nodes[node_num][2].append(lyr)
        lyrs.remove(lyr)
    for node in nodes:
        print node
    #sort layers
    lyrs = sorted(lyrs, key=lambda lyr: lyr[1], reverse = True)

    #allocate layers
    #greedy
    for lyr in lyrs:
        g_nodes = sorted(g_nodes, key = lambda node:node[1])
        g_nodes[0][1] += lyr[1]
        g_nodes[0][2].append(lyr)
    g_nodes = sorted(g_nodes, key = lambda node : node[0])
    print 'greedy: '
    for node in g_nodes:
    #    f.write("%s\n" % node)
        print str(node[0]) + ': ' + str(node[1])
    print 'standard dev: ' + str(std_dev(g_nodes))
    #print results
    #with open('your_file.txt', 'w') as f:
    for node in nodes:
    #    f.write("%s\n" % node)
        print str(node[0]) + ': ' + str(node[1])

    '''print 'kk-greedy mixed: '
    #calculate ideal cap
    boundary = int(sum([lyr[1] for lyr in lyrs]) / len(nodes))
    trap = 0
    
    for i in range(len(nodes)):
        nodes[i][1] += lyrs[0][1]
        nodes[i][2].append(lyrs[0])
        lyrs.remove(lyrs[0])
    
    for lyr in lyrs:
        #print lyr
        idx = 0
        end = False
        while not end:
            plus = nodes[idx][1] + lyr[1]
            if plus <= (boundary + trap) and plus >= boundary - trap:
                nodes[idx][1] += lyr[1]
                nodes[idx][2].append(lyr)
                end = True
            elif plus <= boundary - trap:
                nodes[idx][1] += lyr[1]
                nodes[idx][2].append(lyr)
                end = True
            else:
                if idx == (len(nodes) - 1):
                    idx = 0
                    trap += 1
                else:
                    idx += 1
    for node in nodes:
        print str(node[0]) + ': ' + str(node[1])
    print 'standard dev: ' + str(std_dev(nodes))'''
if __name__ == "__main__":
    main()

