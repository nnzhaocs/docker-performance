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
        datadict['layer transfer and merge time'],
        label='Layer Transfer and Merge Time',
        marker='^',
    )
    ax.set(xlabel='Uncompressed size of the layer (mb)', ylabel='latency (seconds)', title=gname)
    ax.legend()
    ax.grid()
    fig.savefig(gname)
    plt.show()




def main():
    datalist = []
    with open('registry_results_layer_construct.lst', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            datalist.append([float(row[0]), float(row[1]), int(row[4])/(1024*1024)])

    # sort by size parameter
    datalist.sort(key=lambda x: x[2])
    ziplist = list(zip(*datalist))
    datadict = {
        'metadata lookup time': ziplist[0] ,
        'layer transfer and merge time': ziplist[1],
        'uncompressed size': ziplist[2]
    }
    draw_graph(datadict, "Layer Construction Time breakdown on GET")
    
if __name__ == '__main__':
    main()
