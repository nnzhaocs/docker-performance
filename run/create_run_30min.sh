#!/bin/bash

#-----------
# ./create_yaml.sh 
# python create_yaml.py -t dal -m sift -s selective -a 8 -n 7 -c 4
# sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -t 400 -i "docker ps"
#----------

date

echo "testing params:"
#echo $1
echo $2
echo $3
echo $4
echo $5
echo $6
echo $7

codedir="/home/nannan/docker-performance"
testingmachine=3
cachesizeratio=0.25
repullthres=3

echo "cleanup thors..."
./cleanup_thors.sh

echo "sleep 30 s, wait for cleaning"
sleep 30

echo "create config, registry, and client file"
python create_yaml.py -t $2 -m $3 -s $4 -a $5 -n $6 -c $7

echo "cp config.yaml file to other client machines"
sshpass -p 'nannan' pssh -h clients.txt  -l root -A -i "sshpass -p 'nannan' scp nannan@amaranth$testingmachine:$codedir/config.yaml  $codedir/"

echo "sleep 30 s, wait for cp config.yml"
sleep 30

echo "kill all old pythons"
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 'pkill -9 python'

# first run match
cd $codedir

echo "run match"
python master.py -c match -i config.yaml

# second run sift containers
# nnzhaocs/distribution:original
# dedup registries count: 3, 6, 9, 12, 15, 18, 21

# ------------------------------------------

dedupimagearr=("nnzhaocs/distribution:distributionthors3" "nnzhaocs/distribution:distributionthors6" "nnzhaocs/distribution:distributionthors9" "nnzhaocs/distribution:distributionthors12" "nnzhaocs/distribution:distributionthors15" "nnzhaocs/distribution:distributionthors18" "nnzhaocs/distribution:distributionthors21")
declare -A sizearr
sizearr["dal"]=30
sizearr+=(["dev"]=21 ["fra"]=8 ["lon"]=14 ["prestage"]=86 ["stage"]=12 ["syd"]=3)
cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/$6+1"|bc)
echo "cachesize:"
echo $cachesize

echo "start containers ......"

imageno=$(echo "$6/3-1"|bc)

cd $codedir"/run"

echo ${dedupimagearr[$imageno]}
./run_sifttest.sh ${dedupimagearr[$imageno]} dedupregistries.txt $cachesize $repullthres

echo "sleep 20 s, wait for dedup registries to start"
sleep 20

echo "save dedup registry containers' logs"
sshpass -p 'kevin123' pssh -h dedupregistries.txt -l root -A -i 'docker logs -f $(docker ps -a -q) &>> /home/nannan/logs-nondedup &'

echo "sleep 20 s, wait for dedup registries to run a while"
sleep 20

./run_sifttest.sh nnzhaocs/distribution:original primaryregistries.txt $cachesize $repullthres

echo "sleep 20 s, wait for primary registries to start"
sleep 20

echo "start clients .......\n"
echo "warmup ....."
./run_clients.sh config.yaml warmup $codedir clients.txt

echo "sleep 20 s, wait for client to start sending warmup requests"
sleep 20

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

echo "sleep 30 min, wait for warmup to finish"
sleep 1200

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

echo "run ...."
./run_clients.sh config.yaml run $codedir clients.txt

echo "sleep 30 s, wait for client to start sending run requests"
sleep 30
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

echo "sleep 50 min, wait for run to finish"
sleep 3000

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

./get_results_fromclients.sh $testingmachine clients.txt

echo "sleep 20 s, wait for getting clients results.json file"
sleep 20
./get_alllogs_thors.sh $testingmachine
