echo "the input directory is:"
echo $1

cat $1/*.log > $1/logs

awk '/slice construct/{print}' $1/logs > lypredata

### metdata
awk '/metadata lookup time/{print}' lypredata > data
awk -F'metadata lookup time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > metadatalookuptime

### cp time
awk -F'slice construct time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layerconstructtime

### compression time
#awk -F'compression time:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > layercompressiontime

### transfer time
awk -F'transfer time:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > layertransfertime

### compressed size
awk -F'compressed size:' '{print $2}' data > tmp1
awk -F',' '{print $1}' tmp1 > comprslayersize

#### size
#awk -F'uncompressed size:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > uncomprslayersize

paste -d"\t" metadatalookuptime layerconstructtime layertransfertime comprslayersize > $1/registry_results.lst
rm data tmp1 metadatalookuptime layerconstructtime layertransfertime comprslayersize 
cd $1
cp registry_results.lst ../

#paste -d"\t" metadatalookuptime layerconstructtime layertransfertime comprslayersize uncomprslayersize > $1/registry_results.lst  
#rm data tmp1 metadatalookuptime layerconstructtime layertransfertime comprslayersize uncomprslayersize
#cd $1
#cp registry_results.lst ../
