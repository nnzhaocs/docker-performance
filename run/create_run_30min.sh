#!/bin/bash

#-----------
# ./create_yaml.sh 
# python create_yaml.py -t dal -m sift -s selective -a 8 -n 7 -c 4 -p 2
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
echo $8

codedir="/home/nannan/docker-performance"
testingmachine=3
cachesizeratio=0.25
repullthres=3

echo "cleanup thors..."
./cleanup_thors.sh

echo "sleep 10 s, wait for cleaning"
sleep 10

echo "create config, registry, and client file"
python create_yaml.py -t $2 -m $3 -s $4 -a $5 -n $6 -c $7 -p $8

echo "cp config.yaml file to other client machines"
sshpass -p 'nannan' pssh -h clients.txt  -l root -A -i "sshpass -p 'nannan' scp nannan@amaranth$testingmachine:$codedir/config.yaml  $codedir/"

echo "sleep 10 s, wait for cp config.yml"
sleep 10

echo "kill all old pythons"
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 'pkill -9 python'

# first run match
cd $codedir

echo "run match"
python master.py -c match -i config.yaml

# Second run containers
# -----------------------------------------
# nodedup:     nnzhaocs/distribution:original
# primary: b-mode 3:  nnzhaocs/distribution:primary-b-mode3
# restore:
#  (1) nnzhaocs/distribution:distributionthors7
#  (2) nnzhaocs/distribution:distributionthors14
# b-mode 0: 
# nnzhaocs/distribution:b-mode-0 (21 nodes)
# sift: standard:
# nnzhaocs/distribution:primary14 + nnzhaocs/distribution:original
# nnzhaocs/distribution:primary14 + nnzhaocs/distribution:original
# <shrink to 7> 
# sift: selective:
# same as standard
# 
# ------------------------------------------

dedupimagearr=("nnzhaocs/distribution:distributionthors7" "nnzhaocs/distribution:distributionthors14" "nnzhaocs/distribution:distributionthors21")
originalimage="nnzhaocs/distribution:original"
#primaryimagearr=("nnzhaocs/distribution:primarythors7" "nnzhaocs/distribution:primarythors14" "nnzhaocs/distribution:primarythors21")

declare -A sizearr
sizearr["dal"]=20
sizearr+=(["dev"]=13 ["fra"]=6 ["lon"]=10 ["prestage"]=60 ["stage"]=7 ["syd"]=2)

echo "start containers ......"
cd $codedir"/run"

printf "\n\nTESTMODE: %s\n\n" $3

echo "first start dedup containers----------->"

if [ $3 == "restore" ]; then
	cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/$6+1"|bc)
	echo "cachesize:"
	echo $cachesize

	imageno=$(echo "$6/7-1"|bc)
	echo ${dedupimagearr[$imageno]}
	./run_sifttest.sh ${dedupimagearr[$imageno]} dedupregistries.txt $cachesize $repullthres
	echo "sleep 20 s, wait for dedup registries to start"
	sleep 20
	echo "save dedup registry containers' logs"
	sshpass -p 'kevin123' pssh -h dedupregistries.txt -l root -A -i 'docker logs -f $(docker ps -a -q) &>> /home/nannan/logs-nondedup &'

elif [ $3 == "sift" ]; then
	./run_sifttest.sh $originalimage dedupregistries.txt
fi;

echo "sleep 20 s, wait for dedup registries to run a while if any"
sleep 20

echo "second start primary containers----------->"

if [ $3 == "nodedup" ]; then
	./run_sifttest_original.sh $originalimage primaryregistries.txt
elif [ $3 == "sift" ]; then
	./run_sifttest_primary.sh $originalimage primaryregistries.txt 
elif [ $3 == "primary" ]; then
	./run_sifttest_primary.sh $originalimage primaryregistries.txt 
fi;

echo "sleep 20 s, wait for primary registries to start"
sleep 20

echo "start clients .......\n"
echo "warmup ....."
./run_clients.sh config.yaml warmup $codedir clients.txt

echo "sleep 20 s, wait for client to start sending warmup requests"
sleep 20

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

if [ $2 == "prestage" ]; then
	echo "sleep 20 min, wait for warmup to finish"
	sleep 1800
else
	echo "sleep 20 min, wait for warmup to finish"
	sleep 1200
fi;

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

echo "run ...."
./run_clients.sh config.yaml run $codedir clients.txt

echo "sleep 20 s, wait for client to start sending run requests"
sleep 20
sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 50 logs"

echo "sleep 40 min, wait for run to finish"
sleep 2400

sshpass -p 'nannan' pssh -h clients.txt -l nannan -A -i -t 600 "cd $codedir; tail -n 20 logs"

./get_results_fromclients.sh $testingmachine clients.txt

echo "sleep 20 s, wait for getting clients results.json file"
sleep 20
./get_alllogs_thors.sh $testingmachine
