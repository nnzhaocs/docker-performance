
#!/bin/bash

echo "gathering all the container logs from hulks to amaranth$1"
#create a new directory in amaranth with timestamp
dir=$(date +%Y%m%d_%H%M%S)
mkdir -p /home/nannan/testing/resultslogs/$dir
# replace 20190618_164013 with the newly created dir
pssh -h remotehostshulk.txt -l root -A -i "sshpass -p 'nannan' scp /var/lib/docker/containers/*/*-json.log   root@amaranth$1:/home/nannan/testing/resultslogs/$dir"
