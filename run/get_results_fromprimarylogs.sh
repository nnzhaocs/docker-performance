
echo "logs file: "
echo $1
grep "NANNAN: primary: reqtype" $1 > tmp
grep 'reqtype: LAYER,' tmp > data
awk -F'mem time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > memtime

awk -F'ssd time:' '{print $2}' data > tmp1
#awk -F'l' '{print $1}' tmp1 > ssdtime
awk -F',' '{print $1}' tmp1 > ssdtime

awk -F'layer transfer time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > networktime

awk -F'total time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > totaltime

awk -F'size:' '{print $2}' data > tmp1
awk -F'"' '{print $1}' tmp1 > size

paste -d"\t" memtime networktime totaltime size > alltimesize.lst
