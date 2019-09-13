import csv
import matplotlib.pyplot as plt

def draw_graph(datadict, gname):
    '''
    datadict is of the form
    {
        'metadata lookup time': [...],
        'layer transfer merge time': [...],
        'uncompressed size': [...]
    }
    '''
    fig, ax = plt.subplots()
    ax.scatter(
        datadict['uncompressed size'],
        datadict['metadata lookup time'],
        label='Metadata Lookup Time',
        marker='o',
    )
    ax.scatter(
        datadict['uncompressed size'],
        datadict['transfer time'],
        label='Transfer Time',
        marker='s',
    )
    ax.scatter(
        datadict['uncompressed size'],
        datadict['slice construct time'],
        label='Slice Construct Time',
        marker='^',
    )
    ax.set(xlabel='Uncompressed size of the layer (mb)', ylabel='latency (seconds)', title=gname)
    ax.legend()
    ax.grid()
    fig.savefig(gname)
    plt.show()




def main():
    datalist = []
    with open('registry_results_slice_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            datalist.append([float(row[0]), float(row[1]), float(row[2]),
                             int(row[4])/(1024*1024)])

    # sort by size parameter
    datalist.sort(key=lambda x: x[2])
    ziplist = list(zip(*datalist))
    datadict = {
        'metadata lookup time': ziplist[0] ,
        'slice construct time': ziplist[1],
        'transfer time': ziplist[2],
        'uncompressed size': ziplist[3]
    }
    draw_graph(datadict, "Slice Construction Time Breakdown")
    
if __name__ == '__main__':
    main()
