
https://redis.io/topics/quickstart
https://redis.io/topics/cluster-tutorial

example:
sshpass -p 'kevin123' pssh -h remotehostthors.txt -l root -A -i "cd /home/nannan/distribution/run/7000; /home/nannan/redis-stable/src/redis-server redis.conf &"

cd /home/nannan/distribution/run/7000
or 
cd /home/nannan/distribution/run/7001

/home/nannan/redis-stable/src/redis-server redis.conf &
/home/nannan/redis-stable/src/redis-cli --cluster create 192.168.0.170:7000 192.168.0.170:7001 \
    192.168.0.171:7000 192.168.0.171:7001 \
    192.168.0.172:7000 192.168.0.172:7001 \
    192.168.0.174:7000 192.168.0.174:7001 \
    192.168.0.176:7000 192.168.0.176:7001 \
    192.168.0.177:7000 192.168.0.177:7001 \
    192.168.0.178:7000 192.168.0.178:7001 \
    192.168.0.179:7000 192.168.0.179:7001 \
    192.168.0.180:7000 192.168.0.180:7001 \
    --cluster-replicas 2

