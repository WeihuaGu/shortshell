#!/bin/bash
let "sum=0"
while true
do
sleep 1500
espeak -vzh 
while let "sum<1000"
do
let "sum++"
xset dpms force off
done
let "sum=0"
done

