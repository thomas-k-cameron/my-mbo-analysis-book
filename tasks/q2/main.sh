mkdir /tmp/input
mkdir /tmp/output
ls /tmp

for file in ${DATA[@]}; do
    aws s3api get-object --bucket compute-assets-36607b9c2d934caa8bf7d19e0251bab6 --key $file /tmp/input/$(python3 ./outfilename.py $file) &
    
done
for file in ${LABELS[@]}; do
    aws s3api get-object --bucket compute-assets-36607b9c2d934caa8bf7d19e0251bab6 --key $file /tmp/input/$(python3 ./outfilename.py $file) &
done
wait
zstd -d --rm /tmp/input/*

python3 main.py
rm -r /tmp/*