# ignore 50mb

echo "testing different modes -------->"
echo "test original registry"
#./create_run_30min.sh 50mb fra nodedup standard 48 0 4 2 &> resultsfra_original.log
echo "test b-mode 3"
#./create_run_30min.sh 50mb fra primary standard 48 0 4 2 &> resultsfra-b-mode-3.log
echo "test b-mode 0"
#./create_run_30min.sh 50mb fra restore standard 48 21 4 2 &> resultsfra-b-mode-0.log
echo "test b-mode 1 (14 primary nodes)"
#./create_run_30min.sh 50mb fra sift standard 48 7 4 1 &> resultsfra-b-mode-1.log
echo "test b-mode 2 (14 primary nodes)" 
./create_run_30min.sh 50mb fra sift standard 48 7 4  2 &> resultsfra-b-mode-2.log
echo "test s-mode"
./create_run_30min.sh 50mb fra sift selective 48 7 4 2 &> resultsfra-s-mode.log

echo "testing restoring performance--------->"
echo "test restore with 14"
#./create_run_30min.sh 50mb fra restore standard 48 14 4 2 &> resultsfra.log
echo "test restore with 7"
#./create_run_30min.sh 50mb fra restore standard 48 7 4 2 &> resultsfra-restore-7.log



