echo "the input directory is:"
echo $1

cat $1/*.log > $1/logs
### metdata
awk '/metadata lookup time/{print}' $1/logs > data
awk -F'metadata lookup time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > metadatalookuptime

### cp time
awk -F'cp time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layercpiotime

### compression time
awk -F'compression time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layercompressiontime

### transfer time
awk -F'transfer time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layerpreparetransfertime

### compressed size
awk -F'slice compressed size:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > comprslayersize

### size
awk -F'slice uncompressed size%!\(EXTRA int64=' '{print $2}' data > tmp1
awk -F'\)' '{print $1}' tmp1 > uncomprslayersize

paste -d"\t" metadatalookuptime layercpiotime layercompressiontime layerpreparetransfertime comprslayersize uncomprslayersize > $1/registry_results.lst  
rm data tmp1 metadatalookuptime layercpiotime layercompressiontime layerpreparetransfertime comprslayersize uncomprslayersize
cd $1
cp registry_results.lst ../
