echo "the input directory is:"
echo $1

# grep -A 4 "get dedup registries" *
# grep -A 4 "get primary registries" *

while read p; do
#p='20190915_145107'
	echo "$p"
	cat /home/nannan/testing/resultslogs/$p/*.log > $1/data
	grep "total time:" $1/data > tmp
	grep "reqtype: LAYER" tmp > tmp1
	awk -F'total time:' '{print $2}' tmp1 > time
	awk -F',' '{print $1}' time > totaltime
	mkdir -p $1/$p
	mv totaltime $1/$p
	awk '{ if($1 > 0) sum += $1;if($1>0) n++ } END { if (n > 0) print sum / n; print n; }' $1/$p/totaltime
done <$1/logs






# ******* get layer ********

#grep 'NANNAN: layer construct:' $1/logs > tmp
#cat tmp > data
##grep 'reqtype: LAYER' tmp > data
#echo "layer request"
#grep ', LAYERCONSTRUCT:' data > tmp
#awk -F'metadata lookup time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > metadatalookuptime
#echo $metadatalookuptime
#awk -F'layer transfer and merge time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > layerconstructtime
#
#awk -F'layer transfer time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > layertransfertime
#
#awk -F'compressed size:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > comprssize
#
#awk -F'uncompressed size:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > uncomprssize
#
#awk -F'compressratio:' '{print $2}' tmp > tmp1
#awk -F'\' '{print $1}' tmp1 > comprsratio
#
#paste -d"\t" metadatalookuptime layerconstructtime layertransfertime comprssize uncomprssize comprsratio > $1/registry_results_layer_construct.lst
#
#echo "layer waiting"
#grep ', WAITLAYERCONSTRUCT:' data > tmp
#
##wk -F'metadata lookup time:' '{print $2}' tmp > tmp1
##awk -F',' '{print $1}' tmp1 > metadatalookuptime
#
#awk -F'layer transfer and merge time:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > layerconstructtime
#
#awk -F'layer transfer time:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > layertransfertime
#
#awk -F'compressed size:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > comprssize
#
#awk -F'uncompressed size:' '{print $2}' data > tmp1
#awk -F',' '{print $1}' tmp1 > uncomprssize
#
#awk -F'compressratio:' '{print $2}' data > tmp1
#awk -F'\' '{print $1}' tmp1 > comprsratio
#
#paste -d"\t" layerconstructtime layertransfertime comprssize uncomprssize comprsratio > $1/registry_results_layer_waitconstruct.lst
#
## ********* get slice ***********
#echo "slice construct:"
#grep 'NANNAN: slice construct:' $1/logs > tmp
#cat tmp > data
##grep 'reqtype: SLICE' tmp > data
#
#grep ', SLICECONSTRUCT:' data > tmp
#
#awk -F'metadata lookup time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > metadatalookuptime
#
#awk -F'slice construct time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > sliceconstructtime
#
#awk -F'transfer time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > slicetransfertime
#
#awk -F'compressed size:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > comprssize
#
#awk -F'uncompressed size:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > uncomprssize
#
#awk -F'compressratio:' '{print $2}' tmp > tmp1
#awk -F'\' '{print $1}' tmp1 > comprsratio
#
#paste -d"\t" metadatalookuptime sliceconstructtime slicetransfertime comprssize uncomprssize comprsratio > $1/registry_results_slice_construct.lst
#
## ********* get dedup times ***********
#echo "dedup layers:"
#grep 'NANNAN: Dodedup:' $1/logs > tmp
#
#
#awk -F'decompression time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > decompressiontime
#
#awk -F'dedup remove dup file time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > removeduptime
#
#awk -F'dedup set recipe time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > setrecipetime
#
#awk -F'slice forward time:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > slicefortime
#
#awk -F'compressed size:' '{print $2}' tmp > tmp1
#awk -F',' '{print $1}' tmp1 > comprssize
#
#awk -F'uncompression size:' '{print $2}' tmp > tmp1
#awk -F'\' '{print $1}' tmp1 > comprsratio
#
#paste -d"\t"  decompressiontime removedupime setrecipetime slicefortime comprssize uncomprssize comprsratio > $1/registry_results_dedup_construct.lst
#
#rm -f metadatalookuptime *time *ratio *size tmp* data 
#
#cd $1
#cp registry_results_layer_construct.lst ../
#cp registry_results_slice_construct.lst ../
#cp registry_results_layer_waitconstruct.lst ../
#









