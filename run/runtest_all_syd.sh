# ignore 50mb

echo "testing different modes -------->"
echo "test original registry"
./create_run_30min.sh 50mb syd nodedup standard 60 0 4 2 &> resultssyd_original.log
echo "test b-mode 3"
./create_run_30min.sh 50mb syd primary standard 60 0 4 2 &> resultssyd-b-mode-3.log
echo "test b-mode 0"
./create_run_30min.sh 50mb syd restore standard 60 21 4 2 &> resultssyd-b-mode-0.log
echo "test b-mode 1 (14 primary nodes)"
./create_run_30min.sh 50mb syd sift standard 60 7 4 1 &> resultssyd-b-mode-1.log
echo "test b-mode 2 (14 primary nodes)" 
./create_run_30min.sh 50mb syd sift standard 60 7 4  2 &> resultssyd.log
echo "test s-mode"
./create_run_30min.sh 50mb syd sift selective 60 7 4 2 &> resultssyd-s-mode.log

echo "testing restoring performance--------->"
echo "test restore with 14"
./create_run_30min.sh 50mb syd restore standard 60 14 4 2 &> resultssyd.log
echo "test restore with 7"
./create_run_30min.sh 50mb syd restore standard 60 7 4 2 &> resultssyd-restore-7.log



