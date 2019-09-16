
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'docker stop $(docker ps -a -q)'
sleep 2
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'docker rm $(docker ps -a -q)'
sleep 2
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'docker ps -a'
sleep 2
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'ls /var/lib/docker/containers/'
sleep 3
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/tmpfs/*'
sleep 3
sshpass -p 'nannan' pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/layers/*'
sleep 5
#rm ~/testing/realblobtraces/*

./flushall-cluster.sh 192.168.0.170
