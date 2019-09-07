
#!/bin/bash

###: ========== run original image ==================
#1. 3-way replication
#2. random read
#1. launch redis from each server
#2. launch original image from each server
# example
#./run_sifttest.sh nnzhaoxxxx remotehostsxxxx
####:============ run sift registry cluster======================######
#1. one cluster: original registry with local redis
#2. dedup cluster: sift image
# ./run_sifttest.sh nnzhaocs/distribution:original remotehostshulksnodedup.txt
# ./run_sifttest.sh nnzhaocs/distribution:distributionhulks0-4 remotehostshulksdedup.txt

####=================== END ==============================#####

echo "Hello! You have many Docker image choices: "

#echo "If you wanna run original registry, plz use: nnzhaocs/distribution:original"
#echo "If you wanna run sift registry, with hulks, plz use: nnzhaocs/distribution:distributioncache"
#echo "If you wanna run sift registry, with thors, plz use: nnzhaocs/distribution:distributionthors" 

cmd=$(printf "The input parameters: %s %s %s %s" $1 $2 $3 $4)
echo $cmd

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
sshpass -p 'kevin123' pssh -h $2 -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd

echo "GET IP FROM HULKS"
hulkip="\$(ip -4 addr |grep 192.168. |grep -Po 'inet \K[\d.]+')"
echo $hulkip

echo "GET IP FROM THORS"
thorip="\$(ip -4 addr |grep 192.168.0.2 |grep -Po 'inet \K[\d.]+')"
echo $thorip

hostip=$thorip
cmd=$(printf "!!!!! You are choosing to using Hostip: %b, 192.168.xxx.xxx is hulks, and 192.168.0.2xx is thors" "$hostip")
echo $cmd

filecachecap=$3 #203 #3524
layercachecap=$3 #203 #3524
stype="MB" #"B"
repullcntthres=$4
comprlevel=4
layerslicingfcntthres=7
layerslicingdirsizethres=5 
ttl=7000
compressmethod="pgzip"
redisaddr="192.168.0.220:6379"


echo 'run containers as following'
cmd1=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=%s\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=$filecachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=$layercachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=10\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=$ttl\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_STYPE=$stype\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_REPULLCNTTHRES=$repullcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSLEVEL=$comprlevel\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGFCNTTHRES=$layerslicingfcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGDIRSIZETHRES=$layerslicingdirsizethres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSMETHOD=$compressmethod\" -e \"REGISTRY_REDIS_ADDR=%s\" --name registry-cluster %s" "$hostip" $redisaddr $1)

cmd2=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_REDIS_ADDR=%s:6379\" --name registry-cluster %s" "$hostip" $1)

cmd3="docker run --rm -d -p 6379:6379 --name redis-rejson redislabs/rejson:latest"

#cmd3=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/diskcache -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168.0.2 |grep -Po \"inet \K[\d.]+\")\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=40000\" --name registry-cluster %s" $1)


cmd4=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/diskcache  -e \"REGISTRY_STORAGE_CACHE_HOSTIP=%s\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=$filecachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=$layercachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=10\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=$ttl\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_STYPE=$stype\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_REPULLCNTTHRES=$repullcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSLEVEL=$comprlevel\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGFCNTTHRES=$layerslicingfcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGDIRSIZETHRES=$layerslicingdirsizethres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSMETHOD=$compressmethod\" -e \"REGISTRY_REDIS_ADDR=%s:6379\" --name registry-cluster %s" "$hostip" "$hostip" $1)

if [ $1 == "nnzhaocs/distribution:original" ]; then 
	cmd=$cmd2
	echo "run redis for each registry"
	echo $cmd3
	sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd3
elif [[ $1 == *primary* ]]; then
	cmd=$cmd4
	echo "run redis for each registry"
	echo $cmd3
	sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd3
fi;
echo $cmd
sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd



