mkdir /tmp/input
mkdir /tmp/output
ls /tmp

for var in ${SIGNAL[@]}; do
    python3 ./main.py $var &
done
wait
rm -r /tmp/*
