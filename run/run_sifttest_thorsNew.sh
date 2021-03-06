
#!/bin/bash

###: ========== build the image ==================

#docker build -t nnzhaocs/distribution:original ./
#docker push nnzhaocs/distribution:original
#pssh -h remotehostshulk.txt -l root -A -i -t 600 'docker pull nnzhaocs/distribution:original'

#rm -rf /home/nannan/dockerimages/docker-traces/data_centers/dal09/prod-dal09-logstash-2017.0*-realblob*
####:============ run and setup registrycluster======================######

echo "Hello! You have two Docker image choices: "

echo "nnzhaocs/distribution:original"
echo "nnzhaocs/distribution:distributioncache"

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
pssh -h remotehostthors.txt -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
pssh -h remotehoststhors.txt -l root -A -i $cmd


filecachecap=66 #3524 # = match result unique dataset size / 8 *0.25
layercachecap=66 #3524# same as above
stype="MB" #"B"
repullcntthres=3
comprlevel=4
layerslicingfcntthres=7
layerslicingdirsizethres=5 #(MB)
ttl=7000
compressmethod="pgzip"

echo 'run containers as following'
cmd1=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168.0.2 |grep -Po \"inet \K[\d.]+\")\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=$filecachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=$layercachecap\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=10\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=$ttl\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_STYPE=$stype\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_REPULLCNTTHRES=$repullcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSLEVEL=$comprlevel\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGFCNTTHRES=$layerslicingfcntthres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_LAYERSLICINGDIRSIZETHRES=$layerslicingdirsizethres\" -e \"REGISTRY_STORAGE_REGISTRYPARAMS_COMPRESSMETHOD=$compressmethod\" --name registry-cluster %s" $1)

#echo "with RAMDISK"
cmd3=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/diskcache -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168.0.2 |grep -Po \"inet \K[\d.]+\")\" -e \"REGISTRY_STORAGE_CACHEPARAMS_FILECACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_LAYERCACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_SLICECACHECAP=291\" -e \"REGISTRY_STORAGE_CACHEPARAMS_TTL=40000\" --name registry-cluster %s" $1)

cmd2=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168.0.2 |grep -Po \"inet \K[\d.]+\")\" --name registry-cluster %s" $1)

if [ $1 == "nnzhaocs/distribution:original" ]; then 
	cmd=$cmd2
else
	cmd=$cmd1	
fi;
echo $cmd
pssh -h remotehostthors.txt -l root -A -i $cmd

