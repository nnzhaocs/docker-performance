
#!/bin/bash

####:============ run primary registry cluster======================######

echo "Hello! "

echo "If you wanna run primary registry, plz use: nnzhaocs/distribution:original"

cmd=$(printf "The input parameters: %s %s %s %s" $1 $2)
echo $cmd

echo "docker pull images: $1"
cmd=$(printf "docker pull %s" $1)
sshpass -p 'kevin123' pssh -h $2 -l root -A -i -t 600 $cmd

echo 'check pulling finishing'
sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd

echo "GET IP FROM HULKS"
hulkip="\$(ip -4 addr |grep 192.168. |grep -Po 'inet \K[\d.]+')"
echo $hulkip

echo "GET IP FROM THORS"
thorip="\$(ip -4 addr |grep 192.168.0.2 |grep -Po 'inet \K[\d.]+')"
echo $thorip


echo "================> manually change here!"

hostip=$thorip
cmd=$(printf "!!!!! You are choosing to using Hostip: %b, 192.168.xxx.xxx is hulks, and 192.168.0.2xx is thors" "$hostip")
echo $cmd

echo 'run containers as following'

cmd3="docker run --rm -d -p 6379:6379 --name redis-rejson redislabs/rejson:latest"

cmd6=$(printf "docker run --rm -d -p 5000:5000 --mount type=tmpfs,destination=/var/lib/registry -e \"REGISTRY_REDIS_ADDR=%s:6379\" --name registry-cluster %s" "$hostip" $1)

cmd=$cmd6
echo "run redis for each registry"
echo $cmd3
sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd3

echo $cmd
sshpass -p 'kevin123' pssh -h $2 -l root -A -i $cmd



