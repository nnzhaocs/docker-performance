# ignore 50mb

echo "testing different modes -------->"
echo "test original registry"
#./create_run_30min.sh 50mb dal nodedup standard 12 0 8 2 &> resultsdal_original.log
echo "test b-mode 3"
#./create_run_30min.sh 50mb dal primary standard 12 0 8 2 &> resultsdal-b-mode-3.log
echo "test b-mode 0"
#./create_run_30min.sh 50mb dal restore standard 12 21 8 2 &> resultsdal-b-mode-0.log
echo "test b-mode 1 (18 primary nodes)"
./create_run_30min.sh 50mb dal sift standard 12 7 8 1 &> resultsdal-b-mode-1.log
echo "test b-mode 2 (18 primary nodes)" 
./create_run_30min.sh 50mb dal sift standard 12 7 8  2 &> resultsdal-b-mode-2.log
echo "test s-mode"
./create_run_30min.sh 50mb dal sift selective 12 7 8 2 &> resultsdal-s-mode.log

echo "testing restoring performance--------->"
echo "test restore with 18"
#./create_run_30min.sh 50mb dal restore standard 12 18 8 2 &> resultsdal-restore-18.log
echo "test restore with 7"
#./create_run_30min.sh 50mb dal restore standard 12 7 8 2 &> resultsdal-restore-7.log



