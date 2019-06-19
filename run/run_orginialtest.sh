###: ========== build the image ==================

docker build -t nnzhaocs/distribution:original ./
docker push nnzhaocs/distribution:original

####:========== cleanup for hulks =============
rm -rf /home/nannan/dockerimages/docker-traces/data_centers/dal09/prod-dal09-logstash-2017.0*-realblob*
pssh -h remotehostshulk.txt -l root -A -i 'docker stop $(docker ps -a -q)'
pssh -h remotehostshulk.txt -l root -A -i 'docker rm $(docker ps -a -q)'
pssh -h remotehostshulk.txt -l root -A -i 'docker ps -a'
pssh -h remotehostshulk.txt -l root -A -i 'ls /var/lib/docker/containers/'
pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/tmpfs/*'
pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/layers/*'

./flushall-cluster.sh 192.168.0.170

####:============ run originalregistrycluster======================######

pssh -h remotehostshulk.txt -l root -A -i 'docker run --rm -d -p 5000:5000 --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/pull_tars/ -v=/home/nannan/testing/layers:/var/lib/registry -e "REGISTRY_STORAGE_CACHE_HOSTIP=$(ip -4 addr |grep 192.168 |grep -Po "inet \K[\d.]+")" --name originalregistry-3  nnzhaocs/distribution:original'

####: =========== collect results ============================== #####
 ####:=========== gether docker logs together and extract results =====================
#create a new directory in amaranth with timestamp
mkdir /home/nannan/testing/resultslogs/$(date +%Y%m%d_%H%M%S)
# replace 20190618_164013 with the newly created dir
pssh -h remotehostshulk.txt -l root -A -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   root@hulk0:/home/nannan/testing/resultslogs/20190618_164013"
