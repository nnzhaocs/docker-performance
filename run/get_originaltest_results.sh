echo "the input directory is:"
echo $1

cat $1/* > $1/logs
### metdata
awk '/metadata lookup time/{print}' logs > data
awk -F'metadata lookup time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > metadatalookuptime
### cp time
#awk '/layer cp time/{print}' logs > data
awk -F'layer cp time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layercpiotime
### transfer time
#awk '/layer transfer time/{print}' logs
awk -F'layer transfer time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layerpreparetransfertime
### size
awk -F'layer size:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layersize

paste -d"\t" metadatalookuptime layercpiotime layerpreparetransfertime layersize > registry_results.lst  
rm data tmp1 logs metadatalookuptime layercpiotime layerpreparetransfertime layersize
cp registry_results.lst ../
