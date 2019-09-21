# ignore $1

echo "testing different modes -------->"
echo "test original registry"
./create_run_30min.sh $1 $2 nodedup standard 12 9 1 2 &> results$1_$2_original.log
echo "test b-mode 3"
./create_run_30min.sh $1 $2 primary standard 12 9 1 2 &> results$1-$2-b-mode-3.log
echo "test b-mode 0"
./create_run_30min.sh $1 $2 restore standard 12 9 1 2 &> results$1-$2-b-mode-0.log

echo "test b-mode 1 (6 primary nodes)"
./create_run_30min.sh $1 $2 sift standard 12 6 1 2 &> results$1-$2-b-mode-1-6.log
echo "test b-mode 2 (6 primary nodes)" 
./create_run_30min.sh $1 $2 sift standard 12 6 1 2 &> results$1-$2-b-mode-2-6.log
echo "test s-mode"
./create_run_30min.sh $1 $2 sift selective 12 6 1 2 &> results$1-$2s-mode-6.log

echo "test b-mode 1 (3 primary nodes)"
./create_run_30min.sh $1 $2 sift standard 12 3 1 2 &> results$1-$2-b-mode-1-3.log
echo "test b-mode 2 (3 primary nodes)"
./create_run_30min.sh $1 $2 sift standard 12 3 1 2 &> results$1-$2-b-mode-2-3.log
echo "test s-mode"
./create_run_30min.sh $1 $2 sift selective 12 3 1 2 &> results$1-$2s-mode-3.log







