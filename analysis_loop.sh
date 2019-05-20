echo "10 percent";
sleep 5;
python analysis.py -i total_trace_splits -c simulate -p 10;
echo "25 percent";
sleep 5;
python analysis.py -i fra02 -c simulate -p 25;
echo "50 percent";
python analysis.py -i fra02 -c simulate -p 50;
echo "75 percent";
python analysis.py -i fra02 -c simulate -p 75;

