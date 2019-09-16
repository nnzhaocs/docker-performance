
#!/bin/bash

####:============ run primary registry cluster======================######

echo "Hello! "

echo "If you wanna run primary registry, plz use: nnzhaocs/distribution:original"
cmd=$(printf "The input parameters: %s %s %s %s" $1 $2 $3 $4)
echo $cmd

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
sshpass -p 'nannan' pssh -h $2 -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
sshpass -p 'nannan' pssh -h $2 -l root -A -i $cmd

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
stype="B" #"MB" #"B"
repullcntthres=$4
comprlevel=4
layerslicingfcntthres=7
layerslicingdirsizethres=5 
ttl=7000
compressmethod="pgzip"
redisaddr="192.168.0.220:6379"

echo 'run containers as following'

cmd3="docker run --rm -d -p 6379:6379 --name redis-rejson redislabs/rejson:latest"

cmd4=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=%s\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=$filecachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=$layercachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=10\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=$ttl\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_STYPE=$stype\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_REPULLCNTTHRES=$repullcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSLEVEL=$comprlevel\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGFCNTTHRES=$layerslicingfcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGDIRSIZETHRES=$layerslicingdirsizethres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSMETHOD=$compressmethod\" -e \"REGISTRY_REDIS_ADDR=%s:6379\" --name registry-cluster %s" "$hostip" "$hostip" $1)

#cmd6=$(printf "docker run --rm -d -p 5000:5000 --mount type=tmpfs,destination=/var/lib/registry -e \"REGISTRY_REDIS_ADDR=%s:6379\" --name registry-cluster %s" "$hostip" $1)

cmd=$cmd4
echo "run redis for each registry"
echo $cmd3
sshpass -p 'nannan' pssh -h $2 -l root -A -i $cmd3

echo $cmd
sshpass -p 'nannan' pssh -h $2 -l root -A -i $cmd



