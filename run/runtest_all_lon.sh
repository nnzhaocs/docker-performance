# ignore 50mb

echo "testing different modes -------->"
echo "test original registry"
./create_run_30min.sh 50mb lon nodedup standard 12 0 4 2 &> resultslon_original.log
echo "test b-mode 3"
./create_run_30min.sh 50mb lon primary standard 12 0 4 2 &> resultslon-b-mode-3.log
echo "test b-mode 0"
./create_run_30min.sh 50mb lon restore standard 12 21 4 2 &> resultslon-b-mode-0.log
echo "test b-mode 1 (14 primary nodes)"
./create_run_30min.sh 50mb lon sift standard 12 7 4 1 &> resultslon-b-mode-1.log
echo "test b-mode 2 (14 primary nodes)" 
./create_run_30min.sh 50mb lon sift standard 12 7 4  2 &> resultslon-b-mode-2.log
echo "test s-mode"
./create_run_30min.sh 50mb lon sift selective 12 7 4 2 &> resultslon-s-mode.log

echo "testing restoring performance--------->"
echo "test restore with 14"
#./create_run_30min.sh 50mb lon restore standard 12 14 4 2 &> resultslon.log
echo "test restore with 7"
#./create_run_30min.sh 50mb lon restore standard 12 7 4 2 &> resultslon-restore-7.log



