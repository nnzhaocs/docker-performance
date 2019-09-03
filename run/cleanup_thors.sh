sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker stop $(docker ps -a -q)'
echo "sleep 10 s"
sleep 10
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker rm $(docker ps -a -q)'
echo "sleep 10 s"
sleep 10
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'docker ps -a'
echo "sleep 10 s"
sleep 10
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'ls /var/lib/docker/containers/'
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'rm -rf /home/nannan/testing/tmpfs/*'
echo "sleep 10 s"
sleep 10
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i 'rm -rf /home/nannan/testing/layers/*'
echo "sleep 10 s"
sleep 10

#rm ~/testing/realblobtraces/*

./flushall-cluster.sh 192.168.0.200

