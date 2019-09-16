#sleep 36000
./create_run_30min.sh 50mb dal nodedup standard 12 21 4 &> resultsdal_nodedup.log
./create_run_30min.sh 50mb dev nodedup standard 120 21 4 &> resultsdev_nodedup.log
./create_run_30min.sh 50mb fra nodedup standard 48 21 4 &> resultsfra_nodedup.log 
#./create_run_30min.sh 50mb lon nodedup standard 12 21 4  &> resultslon_nodedup.log
./create_run_30min.sh 50mb stage nodedup standard 12 21 4 &> resultsstage_nodedup.log
./create_run_30min.sh 50mb syd nodedup standard 60 21 4 &> resultssyd_nodedup.log
./create_run_30min.sh 50mb prestage nodedup standard 22 21 3 &> resultsprestage_nodedup.log
./create_run_30min.sh 50mb dal restore standard 12 14 4 &> resultsdal.log
./create_run_30min.sh 50mb prestage restore standard 22 14 3 &> resultsprestage.log
