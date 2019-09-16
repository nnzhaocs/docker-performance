
#!/bin/bash

echo "gathering all the container logs from hulks to amaranth$1"

echo "get primary registries"
dir=$(date +%Y%m%d_%H%M%S)
echo $dir
mkdir -p /home/nannan/testing/resultslogs/$dir
# replace 20190618_164013 with the newly created dir
sshpass -p 'nannan' pssh -h primaryregistries.txt -l root -A -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   root@amaranth$1:/home/nannan/testing/resultslogs/$dir"

echo "get dedup registries"
dir=$(date +%Y%m%d_%H%M%S)
echo $dir
mkdir -p /home/nannan/testing/resultslogs/$dir
# replace 20190618_164013 with the newly created dir
sshpass -p 'nannan' pssh -h dedupregistries.txt -l root -A -t 600 -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   nannan@amaranth$1:/home/nannan/testing/resultslogs/$dir"



#echo "cping client generated result.json file..."
#sshpass -p 'nannan' scp /home/nannan/testing/results/results.json root@amaranth$1:/home/nannan/testing/resultslogs/$dir
