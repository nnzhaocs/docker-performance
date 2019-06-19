echo "the input directory is:"
echo $1

cat $1/* > $1/total.log
### metdata
awk '/metadata lookup time/{getline;print;}' total.log > data
grep -v "THIS IS" data > tmp
awk -F'[", ]' '{print $5}' tmp > metadatalooup.time.lst
### cp time
awk '/layer cp time/{print}' total.log > data
awk -F' ' '{print $7}' data
### transfer time
awk '/layer transfer time/{print}' total.log


