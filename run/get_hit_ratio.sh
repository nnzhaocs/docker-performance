echo "the input directory is:"
echo $1

cat $1/*.log > $1/logs
### metdata

echo "=====>>> Layer cache statistics <<<===="

hitcnt=$(grep "layer cache hit!" $1/logs | wc -l | cut -f1 -d' ')
echo "layer cache hit count: "$hitcnt

misscnt=$(grep "layer cache miss!" $1/logs | wc -l | cut -f1 -d' ')
echo "layer cache miss count: "$misscnt

stagehitcnt=$(grep "layer stage hit" $1/logs | wc -l | cut -f1 -d' ')
echo "layer stage area hit count: "$stagehitcnt

waitlayercnt=$(grep "layer construct: reqtype: LAYER, WAITLAYERCONSTRUCT" $1/logs | wc -l | cut -f1 -d' ')
echo "waiting for restoring layer count: "$waitlayercnt

cmd=$(printf "scale=3; %d/(%d+%d)"  $hitcnt $hitcnt $misscnt ) 
echo "layer hit ratio: for layer cache + stage area: "$(echo $cmd | bc)

cmd=$(printf "scale=3; (%d+%d)/(%d+%d)" $hitcnt $waitlayercnt $hitcnt $misscnt ) 
echo "layer hit ratio: for layer cache + stage area + waiting: "$(echo $cmd | bc)

echo "=====>>> File cache statistics <<<===="

hitcnt=$(grep "file cache hit" $1/logs | wc -l | cut -f1 -d' ')
echo "file cache hit count: "$hitcnt

misscnt=$(grep "file cache miss" $1/logs | wc -l | cut -f1 -d' ')
echo "file cache miss count: "$misscnt

cmd=$(printf "scale=3; %d/(%d+%d)" $hitcnt $hitcnt $misscnt)
echo "file cache hit ratio: "$(echo $cmd | bc)























