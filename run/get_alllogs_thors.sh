
#!/bin/bash

echo "gathering all the container logs from thors to amaranth$1"
#create a new directory in amaranth with timestamp
dir=$(date +%Y%m%d_%H%M%S)
echo $dir
mkdir -p /home/nannan/testing/resultslogs/$dir
# replace 20190618_164013 with the newly created dir
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -t 400 -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   root@amaranth$1:/home/nannan/testing/resultslogs/$dir"

#echo "cping client generated result.json file..."
#sshpass -p 'nannan' scp /home/nannan/testing/results/results.json root@amaranth$1:/home/nannan/testing/resultslogs/$dir
