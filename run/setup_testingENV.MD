
beware of 174 171 and 172

#git clone docker-performance
git clone https://github.com/nnzhaocs/docker-performance.git

mkdir -p /home/nannan/testing/realblobtraces
mkdir -p /home/nannan/testing/results
mkdir -p /home/nannan/testing/resultslogs

mkdir -p /home/nannan/dockerimages/docker-traces/data_centers
mkdir -p /home/nannan/dockerimages/layers/hulk1
mkdir -p /home/nannan/dockerimages/layers/hulk4

sudo mount 192.168.0.174:/home/nannan/dockerimages/layers /home/nannan/dockerimages/layers/hulk4
sudo mount 192.168.0.171:/home/nannan/dockerimages/layers /home/nannan/dockerimages/layers/hulk1
sudo mount 192.168.0.172:/home/nannan/dockerimages/docker-traces/data_centers/ /home/nannan/dockerimages/docker-traces/data_centers


