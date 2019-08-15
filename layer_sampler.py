import sys
import os
from os.path import stat
from argparse import ArgumentParser
import pickle

layer_files = ["/home/nannan/dockerimages/layers/hulk1/hulk1_layers_less_1g.lst"]#, "/home/nannan/dockerimages/layers/hulk4/hulk4_layers_less_1g.lst"]
out_dir = "/home/nannan/dockerimages/layers/hulk1/"
stored_dat_file = os.getcwd() + "/lyr_size.pkl"
#df_num = 160

def setup():
    print 'entered setup mode, now collecting layer size information...'
    layer_size_dict = {}
    lyrs = []
    lyr_failed = []

    for lyr_f in layer_files:
        with open(lyr_f, 'r') as f:
            content = f.readlines()
            lyrs.extend([x.strip() for x in content])
    
    for lyr in lyrs:
        try:
            size = os.stat(lyr).st_size
            layer_size_dict[lyr] = size
        except:
            lyr_failed.append(lyr)
    
    print 'info collection complete.'
    print 'successfully identified ' + str(len(lyrs)) + ' lyrs'
    print 'failed to get the size of ' + str(len(lyr_failed)) + ' layer files, dump:'
    print lyr_failed

    print 'now writing results to pickle file in current directory...'
    with open(stored_dat_file, 'wb') as f:
        pickle.dump(layer_size_dict, f, pickle.HIGHEST_PROTOCOL)

def sampling(layer_size_dict, size):
    print 'collecting all layers with size close to ' + str(size) + ' MB...'
    res = {}
    cap = size * 1.1
    floor = size * 0.9
    if size == 1:
        floor = 0

    for lyr, lyr_size in layer_size_dict.items():
        mb_size = lyr_size / 1024 / 1024
        if mb_size <= cap and mb_size >= floor :
            res[lyr] = lyr_size
    result = sorted(res, key=res.__getitem__)
    print 'found ' + str(len(result)) + ' layers satisfying the size requirement.'
    print 'writing layer list to hulk1...'
    #print str(res[result[0]])
    #print str(res[result[1]])
    #print str(res[result[-1]])
    with open(out_dir+'hulk_layers_approx_'+str(size)+'MB.lst', 'w') as f:
        for lyr in result:
            f.write("%s\n" % lyr)

def main():
    print 'WARNING: the current running version is tuned for layers no more than 50M.'
    print 'WARNING: now assuming static input output directories (hardcoded)'
    parser = ArgumentParser(description='allow customized sampling args.')
    parser.add_argument('-c', '--command', dest='command', type=str, required=True, 
                        help = 'Mode command. Possible commands: setup, sample.')
    #parser.add_argument('-n', '--number', dest='number', type=int, required=False,
    #                    help = 'For sampling only. Specify number of layers wanted.')
    parser.add_argument('-size', '--size', dest='size', type=int, required=False,
                        help = 'For sampling only. Specify layer size limit.')
    args = parser.parse_args()

    if args.command == 'setup':
        setup()
    elif args.command == 'sample':
        if args.size == None:
            print 'size not specified, quit'
            exit(-1)
        print 'attempting to populate layer:size dictionary...'
        try:
            with open(stored_dat_file, 'rb') as f:
                layer_size_dict = pickle.load(f)
        except:
            print 'unable to read the stored layer:size file'
            exit(-1)
        print 'successfully read in ' + str(len(layer_size_dict)) + ' layers, now sampling...'
        for i in range(60, 210, 10):
            #print i
            sampling(layer_size_dict, i)#args.size)


if __name__ == "__main__":
    main()
