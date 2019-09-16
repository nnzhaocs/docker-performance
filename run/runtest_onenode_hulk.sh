# ignore 50mb
echo $1
echo "testing different modes -------->"
echo "test original registry"
./create_run_30min_onenode_hulk.sh $1 dal nodedup standard 12 0 1 2 &> resultsdal_original.log
echo "test b-mode 3"
./create_run_30min_onenode_hulk.sh $1 dal primary standard 12 0 1 2 &> resultsdal-b-mode-3.log
echo "test b-mode 0 with preconstruct"
./create_run_30min_onenode_hulk.sh $1 dal restore standard 12 1 1 2 preconstruct &> resultsdal-b-mode-0-preconstructcache.log
echo "test b-mode without preconstruct"
./create_run_30min_onenode_hulk.sh $1 dal restore standard 12 1 1 2 nocache  &> resultsdal-b-mode-0-nocache.log
echo "test b-mode without preconstruct with a cache"
./create_run_30min_onenode_hulk.sh $1 dal restore standard 12 1 1 2 normallcache  &> resultsdal-b-mode-0-normalcache.log

mkdir $1
mv *.log  $1
#mv resultsdal_original.log resultsdal-b-mode-3.log resultsdal-b-mode-0.log resultsdal-b-mode-0-no-preconstruct.log $1












