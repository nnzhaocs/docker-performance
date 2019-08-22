
#!/bin/bash


echo "gathering all the results.json from amaranths to amaranth$1"
echo "gathering all client generated result.json file..."
#create a new directory in amaranth with timestamp

dir=$(date +%Y%m%d_%H%M%S)
echo $dir
mkdir -p /home/nannan/testing/results/$dir
# replace 20190618_164013 with the newly created dir
pssh -h remotehostsamaranth.txt -l root -A -i "sshpass -p 'nannan' scp /home/nannan/testing/results/results.json*   root@amaranth$1:/home/nannan/testing/results/$dir"

echo "merging all results.json"
#jq -s 'reduce .[] as $item ({}; . * $item)' /home/nannan/testing/results/$dir/results.json* > all_results.json
jq -s '[.[][]]' /home/nannan/testing/results/$dir/results.json-* > /home/nannan/testing/results/$dir/all_results.json
