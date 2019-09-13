import csv
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np

def draw_graph(lcdict, scdict, ddict, gname):
    the_dicts = [lcdict, scdict, ddict]
    labels = ["Layer", "Slice", "Deduplication"]

    metadatalookup = [d['mean metadata lookup time'] for d in the_dicts]
    layertransferandmerge = [d['mean layer transfer and merge time'] for d in the_dicts]
    sliceconstruct = [d['mean slice construct time'] for d in the_dicts]
    slicetransfer = [d['mean slice transfer time'] for d in the_dicts]
    decompression = [d['mean decompression time'] for d in the_dicts]
    removedup = [d['mean dedup remove dup file time'] for d in the_dicts]
    setrecipe = [d['mean dedup set recipe time'] for d in the_dicts]

        
    
    ind = np.arange(len(labels))
    width = 0.35
    subwidth = width/7
    fig, ax = plt.subplots()
    p1 = plt.bar(ind-(subwidth*3), metadatalookup, subwidth)
    p2 = plt.bar(ind-(subwidth*2), layertransferandmerge, subwidth)
    p3 = plt.bar(ind-(subwidth*1) , sliceconstruct, subwidth)
    p4 = plt.bar(ind, slicetransfer, subwidth)
    p5 = plt.bar(ind+(subwidth*1), decompression, subwidth)
    p6 = plt.bar(ind+(subwidth*2), removedup, subwidth)
    p7 = plt.bar(ind+(subwidth*3), setrecipe, subwidth)

    plt.ylabel("Average Latency (seconds)")
    plt.title("Average Latency Breakdown")
    plt.xticks(ind, labels)
    plt.legend((p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0],),
               ("Metadata Lookup", "Layer Transfer and Merge", "Slice Construction",
                "Slice Transfer", "Decompression", "Removing duplicates", "Setting recipe",)
               )

    fig.savefig(gname)
    plt.show()




def main():
    layerconstructdatadict = {}
    sliceconstructdatadict = {}
    dedupdatadict = {}

    with open('registry_results_layer_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        datalist = []
        for row in reader:
            datalist.append([float(row[0]), float(row[1])])

        ziplist = list(zip(*datalist))
        layerconstructdatadict = {
            'mean metadata lookup time': mean(ziplist[0]) ,
            'mean layer transfer and merge time': mean(ziplist[1]),
            'mean slice construct time': 0,
            'mean slice transfer time': 0,
            'mean decompression time': 0,
            'mean dedup remove dup file time': 0,
            'mean dedup set recipe time': 0,
        }

    with open('registry_results_slice_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        datalist = []
        for row in reader:
            datalist.append([float(row[0]), float(row[1]), float(row[2])])

        ziplist = list(zip(*datalist))
        print(len(ziplist))
        sliceconstructdatadict = {
            'mean metadata lookup time': mean(ziplist[0]) ,
            'mean slice construct time': mean(ziplist[1]),
            'mean slice transfer time': mean(ziplist[2]),
            'mean layer transfer and merge time': 0,
            'mean decompression time': 0,
            'mean dedup remove dup file time': 0,
            'mean dedup set recipe time': 0,
        }

    with open('registry_results_dedup_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        datalist = []
        for row in reader:
            datalist.append([float(row[0]), float(row[1]), float(row[2])])
        ziplist = list(zip(*datalist))
        dedupdatadict = {
            'mean decompression time': mean(ziplist[0]) ,
            'mean dedup remove dup file time': mean(ziplist[1]),
            'mean dedup set recipe time': mean(ziplist[2]),
            'mean metadata lookup time':0 ,
            'mean layer transfer and merge time': 0,
            'mean slice construct time': 0,
            'mean slice transfer time': 0,
            }

    draw_graph(layerconstructdatadict, sliceconstructdatadict, dedupdatadict, "Average Time Breakdown")
    
if __name__ == '__main__':
    main()
