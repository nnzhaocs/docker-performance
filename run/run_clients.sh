
#!/bin/bash

###: ========== run clients on amaranth machines==================
# pssh -h remotehostsamaranth.txt -l root -A -i -t 600 "cd /home/nannan/docker-performance; git pull;"
# example
# git add config_amaranth2.yaml !!!!!!!!
#./run_clients.sh config_amaranth2.yaml warmup /home/nannan/docker-performance/
# ./run_clients.sh config_amaranth2.yaml run /home/nannan/docker-performance/
# check running status
# pssh -h remotehostsamaranth.txt -l nannan -A -i -t 600 'cd /home/nannan/docker-performance; tail -n 20 logs'
####=================== END ==============================#####

echo "Hello! You are gonna start the following clients to do test: "
cat remotehostsamaranth.txt

cmd=$(printf "The input parameters: %s %s %s" "$1" "$2" "$3")
echo $cmd

echo "Update docker-performance repository!"
cmd=$(printf "cd %s; git pull;" $3)
echo $cmd
pssh -h remotehostsamaranth.txt -l nannan -A -i -t 600 $cmd
echo "PUll again!"
pssh -h remotehostsamaranth.txt -l nannan -A -i -t 600 $cmd

cmd=$(printf "cd %s ; python master.py -i %s -c %s &> logs &" $3 $1 $2)
echo $cmd
pssh -h remotehostsamaranth.txt -l nannan -A -i -t 600 $cmd













































