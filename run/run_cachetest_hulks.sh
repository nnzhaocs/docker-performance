
#!/bin/bash

###: ========== build the image ==================

#docker build -t nnzhaocs/distribution:original ./
#docker push nnzhaocs/distribution:original
#pssh -h remotehostshulk.txt -l root -A -i -t 600 'docker pull nnzhaocs/distribution:original'

#rm -rf /home/nannan/dockerimages/docker-traces/data_centers/dal09/prod-dal09-logstash-2017.0*-realblob*
####:============ run originalregistrycluster======================######

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
pssh -h remotehostshulk.txt -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
pssh -h remotehostshulk.txt -l root -A -i $cmd

echo 'run containers as following'
cmd1=$(printf "docker run --rm -d -p 5000:5000 --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/pull_tars/ -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168 |grep -Po \"inet \K[\d.]+\")\" -e \"REGISTRY_STORAGE_BLOBCACHE_SIZE=164\" -e \"REGISTRY_STORAGE_DISKCACHE_SIZE=164\" --name registry-cluster %s" $1)
#cmd1=$(printf "docker run --rm -d -p 5000:5000 -v=/home/nannan/testing/layers:/var/lib/registry -e \"REGISTRY_STORAGE_CACHE_HOSTIP=\$(ip -4 addr |grep 192.168 |grep -Po \"inet \K[\d.]+\")\" -e \"REGISTRY_STORAGE_BLOBCACHE_SIZE=164\" -e \"REGISTRY_STORAGE_DISKCACHE_SIZE=164\" --name registry-cluster %s" $1)
echo $cmd1
pssh -h remotehostshulk.txt -l root -A -i $cmd1








