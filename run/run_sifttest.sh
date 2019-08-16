
#!/bin/bash

###: ========== run original image ==================
#1. 3-way replication
#2. random read
#1. launch redis from each server
#2. launch original image from each server

####:============ run sift registry cluster======================######
#1. one cluster: original registry with local redis
#2. dedup cluster: sift image


####=================== END ==============================#####

echo "Hello! You have two Docker image choices: "

echo "nnzhaocs/distribution:original"
echo "nnzhaocs/distribution:distributioncache"

cmd=$(printf "The input parameters: %s %s" $1 $2)
echo $cmd

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
pssh -h $2 -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
pssh -h $2 -l root -A -i $cmd

echo "GET IP FROM HULKS"
hulkip='ip -4 addr |grep 192.168 |grep -Po \"inet \K[\d.]+\"'
echo $hulkip
echo "GET IP FROM THORS"
#\$(ip -4 addr |grep 192.168.0.2 |grep -Po \"inet \K[\d.]+\")\"
thorip="\$(ip -4 addr |grep 192.168.0.2 |grep -Po 'inet \K[\d.]+')"
echo $thorip

filecachecap=203 #3524
layercachecap=203 #3524
stype="MB" #"B"
repullcntthres=3
comprlevel=4
layerslicingfcntthres=7
layerslicingdirsizethres=5 #(MB)
ttl=7000
compressmethod="pgzip"
hostip=$thorip

cmd=$(printf "Hostip: %b" "$hostip")
echo $cmd

echo 'run containers as following'
cmd1=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=%s\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=$filecachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=$layercachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=10\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=$ttl\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_STYPE=$stype\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_REPULLCNTTHRES=$repullcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSLEVEL=$comprlevel\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGFCNTTHRES=$layerslicingfcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGDIRSIZETHRES=$layerslicingdirsizethres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSMETHOD=$compressmethod\" --name registry-cluster %s" "$thorip" $1)

cmd2=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_REDIS_ADDR=%s\" --name registry-cluster %s" $hulkip $1)

cmd3="docker run -p 6379:6379 --name redis-rejson redislabs/rejson:latest"

if [ $1 == "nnzhaocs/distribution:original" ]; then 
	cmd=$cmd2
	echo "run redis for each registry"
	pssh -h $2 -l root -A -i $cmd3
else
	cmd=$cmd1	
fi;
echo $cmd
pssh -h $2 -l root -A -i $cmd

