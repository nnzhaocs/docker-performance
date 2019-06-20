###: ========== build the image ==================

#docker build -t nnzhaocs/distribution:original ./
#docker push nnzhaocs/distribution:original
#pssh -h remotehostshulk.txt -l root -A -i -t 600 'docker pull nnzhaocs/distribution:original'

#rm -rf /home/nannan/dockerimages/docker-traces/data_centers/dal09/prod-dal09-logstash-2017.0*-realblob*
####:============ run originalregistrycluster======================######
if [ $1 == "run" ]; then
    echo "in run mode"
    pssh -h remotehostshulk.txt -l root -A -i 'docker run --rm -d -p 5000:5000 --mount type=bind,source=/home/nannan/testing/tmpfs,target=/var/lib/registry/docker/registry/v2/pull_tars/ -v=/home/nannan/testing/layers:/var/lib/registry -e "REGISTRY_STORAGE_CACHE_HOSTIP=$(ip -4 addr |grep 192.168 |grep -Po "inet \K[\d.]+")" --name withcacheregistry-3  nnzhaocs/distribution:cache'
####:=========== gather docker logs together and extract results =====================
else
    echo "in info gathering mode"
    #create a new directory in amaranth with timestamp
    $dir = $(date +%Y%m%d_%H%M%S)
    mkdir -p /home/nannan/testing/resultslogs/$dir
    # replace 20190618_164013 with the newly created dir
    pssh -h remotehostshulk.txt -l root -A -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   root@amaranth1:/home/nannan/testing/resultslogs/$dir"
fi;
