
#!/bin/bash


#./get_results_fromclients.sh 3 remotehostsamaranthsfirst3.txt
echo "gathering all the results.json from amaranths to amaranth$1"
echo "gathering all client generated result.json file..."
#create a new directory in amaranth with timestamp

dir=$(date +%Y%m%d_%H%M%S)
echo $dir
mkdir -p /home/nannan/testing/results/$dir
# replace 20190618_164013 with the newly created dir
sshpass -p 'kevin123' pssh -h $2 -l root -A -i "sshpass -p 'nannan' scp /home/nannan/testing/results/results.json*   root@amaranth$1:/home/nannan/testing/results/$dir"

echo "merging all results.json"
#jq -s 'reduce .[] as $item ({}; . * $item)' /home/nannan/testing/results/$dir/results.json* > all_results.json
jq -s '[.[][]]' /home/nannan/testing/results/$dir/results.json-* > /home/nannan/testing/results/$dir/all_results.json

python get_client_results.py -i /home/nannan/testing/results/$dir
