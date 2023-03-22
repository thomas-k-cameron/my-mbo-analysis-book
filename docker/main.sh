python3 /root/download_files.py
python3 /root/main.py

aws s3 cp /tmp/output/buy.model 
aws s3 cp /tmp/output/sell.model