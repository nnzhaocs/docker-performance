sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker stop $(docker ps -a -q)'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker rm $(docker ps -a -q)'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker ps -a'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'ls /var/lib/docker/containers/'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'rm -rf /home/nannan/testing/tmpfs/*'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'rm -rf /home/nannan/testing/layers/*'

#rm ~/testing/realblobtraces/*

./flushall-cluster.sh 192.168.0.200

