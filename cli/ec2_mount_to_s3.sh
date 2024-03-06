wget https://s3.amazonaws.com/mountpoint-s3-release/latest/x86_64/mount-s3.rpm
sudo yum install ./mount-s3.rpm -y
mkdir data
sudo mount -t s3fs mountpoint-s3-release data