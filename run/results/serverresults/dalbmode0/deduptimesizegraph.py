import csv
import matplotlib.pyplot as plt

def draw_graph(datadict, gname):
    fig, ax = plt.subplots()
    ax.scatter(
        datadict['uncompressed size'],
        datadict['dedup remove dup file time'],
        label='Time to remove duplicate files',
        marker='s',
    )
    ax.scatter(
        datadict['uncompressed size'],
        datadict['dedup set recipe time'],
        label='Time to set recipes',
        marker='^',
    )
    ax.scatter(
        datadict['uncompressed size'],
        datadict['decompression time'],
        label='Decompression time',
        marker='o',
    )
    ax.set(xlabel='Uncompressed size of the layer (mb)', ylabel='latency (seconds)', title=gname)
    ax.legend()
    ax.grid()
    fig.savefig(gname)
    plt.show()




def main():
    datalist = []
    with open('registry_results_dedup_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            datalist.append([float(row[0]), float(row[1]), float(row[2]), 
                             int(row[5])/(1024*1024)])

    # sort by size parameter
    datalist.sort(key=lambda x: x[2])
    ziplist = list(zip(*datalist))
    datadict = {
        'decompression time': ziplist[0] ,
        'dedup remove dup file time': ziplist[1],
        'dedup set recipe time': ziplist[2],
        'uncompressed size': ziplist[3]
    }
    draw_graph(datadict, "Deduplication Time Breakdown")
    
if __name__ == '__main__':
    main()
