#!/bin/bash

#-----------
# ./create_yaml.sh 
# python create_yaml.py -t dal -m sift -s selective -a 8 -n 7 -c 4 -p 2
# sshpass -p 'nannan' pssh -h remotehostthors.txt -l root -A -t 400 -i "docker ps"
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
echo $9

codedir="/home/nannan/docker-performance"
testingmachine=3
cachesizeratio=0.25
repullthres=1

echo "cleanup thors..."
./cleanup_hulks.sh

echo "sleep 10 s, wait for cleaning"
sleep 10

echo "create config, registry, and client file"
python create_yaml_onenode_hulk.py -r $1 -t $2 -m $3 -s $4 -a $5 -n $6 -c $7 -p $8

echo "cp config.yaml file to other client machines"
sshpass -p 'nannan' pssh -h clients.txt  -l root -A -i "sshpass -p 'nannan' scp nannan@amaranth$testingmachine:$codedir/config.yaml  $codedir/"

echo "sleep 10 s, wait for cp config.yml"
sleep 10

echo "kill all old pythons"
sshpass -p 'nannan' pssh -h clients.txt -l root -A -i -t 600 'pkill -9 python'

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
echo $9
if [ $3 == "restore" ] && [ $9 == "preconstruct" ]; then
		cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/$6+1"|bc)
		echo "cachesize:"
		echo $cachesize

		imageno=$(echo "$6/7-1"|bc)
		#echo ${dedupimagearr[$imageno]}
		./run_sifttest_hulks.sh nnzhaocs/distribution:onenodepreconstructhulk  dedupregistries.txt $cachesize $repullthres
		echo "sleep 20 s, wait for dedup registries to start"
		sleep 20
		echo "save dedup registry containers' logs"
		sshpass -p 'nannan' pssh -h dedupregistries.txt -l root -A -i 'docker logs -f $(docker ps -a -q) &>> /home/nannan/logs-nondedup &'
		#sleep 20 
		#echo "sleep 20 s, wait for dedup registries to start"
		#./run_sifttest_restore.sh $originalimage dedupregistries.txt
		#no preconstruct
elif [ $3 == "restore" ] && [ $9 == "nocache" ]; then
		cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/$6+1"|bc)
                echo "cachesize:"
                echo $cachesize
                #imageno=$(echo "$6/7-1"|bc)
		./run_sifttest_hulks.sh nnzhaocs/distribution:onenowithoutdepreconstructhulk  dedupregistries.txt $cachesize $repullthres
elif [ $3 == "restore" ] && [ $9 == "normallcache" ]; then
	# no cache
        cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/$6+1"|bc)
        echo "cachesize:"
        echo $cachesize
        #imageno=$(echo "$6/7-1"|bc)
        ./run_sifttest_hulks.sh nnzhaocs/distribution:normallcachehulk dedupregistries.txt $cachesize $repullthres


elif [ $3 == "sift" ]; then
	./run_sifttest_original.sh $originalimage dedupregistries.txt
fi;

echo "sleep 20 s, wait for dedup registries to run a while if any"
sleep 20

echo "second start primary containers----------->"

if [ $3 == "nodedup" ]; then
	#./run_sifttest_original.sh $originalimage primaryregistries.txt
       #cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/1+1"|bc)
       #echo "cachesize:"
       #echo $cachesize
       newcachesize=100 #$(echo "$cachesize"|bc) #100B
       echo $newcachesize
       ./run_sifttest_inmemory_nodedup_hulks.sh nnzhaocs/distribution:inmemoryonenodehulk primaryregistries.txt $newcachesize $repullthres

elif [ $3 == "sift" ]; then
	./run_sifttest_primary.sh $originalimage primaryregistries.txt 
elif [ $3 == "primary" ]; then
	#./run_sifttest_primary.sh $originalimage primaryregistries.txt 
	#echo $inmemoryimage
	cachesize=$(echo "${sizearr[$2]}*1024*$cachesizeratio/1+1"|bc)
	echo "cachesize:"
	echo $cachesize
	newcachesize=$(echo "$cachesize"|bc)
	echo $newcachesize
        ./run_sifttest_inmemory_hulk.sh nnzhaocs/distribution:inmemoryonenodehulk primaryregistries.txt $newcachesize $repullthres
	#./run_sifttest_inmemory.sh nnzhaocs/distribution:inmemoryonenodesmall4 primaryregistries.txt $newcachesize $repullthres
fi;

echo "sleep 20 s, wait for primary registries to start"
sleep 20

echo "start clients .......\n"
echo "warmup ....."
./run_clients_hulks.sh config.yaml warmup $codedir clients.txt

echo "sleep 20 s, wait for client to start sending warmup requests"
sleep 20

sshpass -p 'nannan' pssh -h clients.txt -l root -A -i -t 600 "cd $codedir; tail -n 50 logs"

if [ $3 == "restore" ]; then
	echo "sleep 20 min, wait for warmup to finish"
	sleep 300
else
	echo "sleep 20 min, wait for warmup to finish"
	sleep 200
fi;

sshpass -p 'nannan' pssh -h clients.txt -l root -A -i -t 600 "cd $codedir; tail -n 20 logs"

echo "run ...."
./run_clients_hulks.sh config.yaml run $codedir clients.txt

echo "sleep 20 s, wait for client to start sending run requests"
sleep 20
sshpass -p 'nannan' pssh -h clients.txt -l root -A -i -t 600 "cd $codedir; tail -n 50 logs"

#echo "sleep 10 min, wait for run to finish"
#sleep 660
if [ $3 == "restore" ]; then
	echo "sleep 40 min, wait for run to finish"
	sleep 2400
else
        echo "sleep 20 min, wait for run to finish"
        sleep 1200
fi;

sshpass -p 'nannan' pssh -h clients.txt -l root -A -i -t 600 "cd $codedir; tail -n 20 logs"

./get_results_fromclients_hulks.sh $testingmachine clients.txt

echo "sleep 20 s, wait for getting clients results.json file"
sleep 20
./get_alllogs_hulks.sh $testingmachine
