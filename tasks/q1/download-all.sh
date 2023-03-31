mkdir /tmp/input
mkdir /tmp/ouput
aws s3 cp s3://compute-assets-36607b9c2d934caa8bf7d19e0251bab6/artifacts/order_classification/ /tmp/input/ --recursive --no-progress &
aws s3 cp s3://compute-assets-36607b9c2d934caa8bf7d19e0251bab6/artifacts/product_info/ /tmp/input/ --recursive --no-progress &
wait
zstd -d --rm -8 /tmp/input/*
