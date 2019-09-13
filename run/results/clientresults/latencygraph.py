import sys
import os
import json 
from argparse import ArgumentParser
import matplotlib.pyplot as plt

def stats(data, graphname):
    fig, ax = plt.subplots()
    markers = ['o', '*', '^', 's']
    # i is only used to change the markers in the scatter plot
    i = 0
    for fname, responses in data:
        size_latency_pairs = []
        for response in responses:
            if response['type'] == 'LAYER':
                size_latency_pairs.append((response['size']/(1024*1024), response['duration']))

        size_latency_pairs.sort(key = lambda x: x[0])
        zippedlist = list(zip(*size_latency_pairs))
        ax.scatter(zippedlist[0], zippedlist[1], label=fname, marker=markers[i])
        i += 1
    ax.set(xlabel='size of layers (mb)', ylabel='latency (seconds)', title='latency for different layer sizes: '+graphname)
    ax.grid()
    ax.legend()
    fig.savefig(graphname[:])
    plt.show()




def main():
    parser = ArgumentParser(description='Input json file name')
    parser.add_argument('-i', '--inputs', dest='inputs', nargs='+', required=True,
                                    help = 'input the json files that contain the data for the scatter plot')
    parser.add_argument('-n', '--name', dest='gname', required=True, help='A name for the graph')

    args = parser.parse_args()
    fnames = args.inputs
    gname = args.gname
    data = []
    for fname in fnames:
        with open(fname, 'r') as fp:
            data.append((fname[:-5], json.load(fp)))
    
    stats(data, gname)
   

if __name__ == "__main__":
    main()
