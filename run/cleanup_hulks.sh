
pssh -h remotehostshulk.txt -l root -A -i 'docker stop $(docker ps -a -q)'
pssh -h remotehostshulk.txt -l root -A -i 'docker rm $(docker ps -a -q)'
pssh -h remotehostshulk.txt -l root -A -i 'docker ps -a'
pssh -h remotehostshulk.txt -l root -A -i 'ls /var/lib/docker/containers/'
pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/tmpfs/*'
pssh -h remotehostshulk.txt -l root -A -i 'rm -rf /home/nannan/testing/layers/*'

rm ~/testing/realblobtraces/*

./flushall-cluster.sh 192.168.0.170
