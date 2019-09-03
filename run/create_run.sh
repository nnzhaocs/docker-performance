#!/bin/bash

#-----------
# ./create_yaml.sh 
# python create_yaml.py -r 50mb -t dal -m sift -s selective -a 8 -n 7 -c 4
#----------

date

echo "testing params:"
echo $1
echo $2
echo $3
echo $4
echo $5
echo $6
echo $7
echo $8

codedir="/home/nannan/docker-performance"
testingmachine=3
cachesizeratio=0.25

echo "cleanup thors\n"
./cleanup_thors.sh

echo "create config, registry, and client file\n"
python create_yaml.py -r $1 -t $2 -m $3 -s $4 -a $5 -n $6 -c $7

echo "cp config.yaml file to other client machines \n"
sshpass -p 'nannan' pssh -h clients.txt  -l root -A -i "sshpass -p 'nannan' scp nannan@amaranth$testingmachine:$codedir/config.yaml  $codedir/"

echo "kill all old pythons"
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 'pkill -9 python'

# first run match
cd $codedir

echo "run match\n"
python master.py -c match -i config.yaml

# second run sift containers
# nnzhaocs/distribution:original
# dedup registries count: 3, 6, 9, 12, 15, 18, 21

dedupimagearr=("nnzhaocs/distribution:distributionthors3" "nnzhaocs/distribution:distributionthors6" "nnzhaocs/distribution:distributionthors9" "nnzhaocs/distribution:distributionthors12" "nnzhaocs/distribution:distributionthors15" "nnzhaocs/distribution:distributionthors18" "nnzhaocs/distribution:distributionthors21")
declare -A sizearr
sizearr["dal"]=6.583
sizearr+=(["dev"]=4.743 ["fra"]=2.351 ["lon"]=3.955 ["prestage"]=20.679 ["stage"]=2.821 ["syd"]=0.875)

cachesize=$(echo "${sizearr[$1]}*1024*$cachesizeratio/$6+1"|bc)
echo "cachesize:"
echo $cachesize

echo "start containers ......\n"

imageno=$(echo "$6/3-1"|bc)

cd $codedir"/run"

echo ${dedupimagearr[$imageno]}
./run_sifttest.sh ${dedupimagearr[$imageno]} dedupregistries.txt $cachesize

echo "sleep 20 s"
sleep 20

./run_sifttest.sh nnzhaocs/distribution:original primaryregistries.txt $cachesize

echo "start clients .......\n"
echo "warmup ....."
./run_clients.sh config.yaml warmup $codedir clients.txt

echo "sleep 20 s"
sleep 20

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

echo "sleep 10 min"
sleep 600

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

echo "run ...."
./run_clients.sh config.yaml run $codedir clients.txt

echo "sleep 30 s"
sleep 30
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

echo "sleep 45 min"

sleep 2700

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

./get_results_fromclients.sh $testingmachine clients.txt


