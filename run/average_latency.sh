
awk '
BEGIN {FS=OFS="\t"}
{
for(i=0;i<=NF;i++)
     {sum[i]=$i;}
     print $0,"sum:"sum
print "avg:"sum/NR
}' $1
