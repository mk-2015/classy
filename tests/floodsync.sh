#!/bin/bash

LIMIT=100
IP="192.168.1.66"
PORT="8080"

echo > out.txt

for (( NUMBER=0; NUMBER<=LIMIT; NUMBER++ ))
do
    curl "http://$IP:$PORT/test/prime/$NUMBER" >> out.txt 2>&1 &
    curl "http://$IP:$PORT/test/prime/$NUMBER" >> out.txt 2>&1 &
    curl "http://$IP:$PORT/test/prime/$NUMBER" >> out.txt 2>&1 &
    curl "http://$IP:$PORT/test/prime/$NUMBER" >> out.txt 2>&1 &
    curl "http://$IP:$PORT/test/prime/$NUMBER" >> out.txt 2>&1 &
    echo 
done

wait