echo "the input directory is:"
echo $1

#cat $1/*.log > $1/logs
### metdata
echo "file cache hit count"
hitcnt=$(grep "file cache hit" $1/logs | wc -l | cut -f1 -d' ')
echo $hitcnt
echo "file cache miss count"
misscnt=$(grep "file cache miss" $1/logs | wc -l | cut -f1 -d' ')
echo $misscnt

echo "file cache hit ratio:"
cmd=$(printf "scale=3; %d/(%d+%d)" $hitcnt $hitcnt $misscnt) 
echo $cmd | bc

echo "slice cache hit count"
hitcnt=$(grep "slice cache hit" $1/logs | wc -l | cut -f1 -d' ')
echo $hitcnt
echo "slice cache miss count"
misscnt=$(grep "slice cache miss" $1/logs | wc -l | cut -f1 -d' ')
echo $misscnt

echo "slice cache hit ratio:"
cmd=$(printf "scale=3; %d/(%d+%d)" $hitcnt $hitcnt $misscnt)
echo $cmd | bc























