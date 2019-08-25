#! /bin/bash
ps ax | grep "tcpreplay" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    file=`shuf -i 1-10 -n 1`.pcapng
    myif=``
    myip=``
    mymac=``
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/iot/data/$file > /tmp/data.pcapng
    tcprewrite --infile=/tmp/data.pcapng --outfile=/tmp/temp1.pcap --srcipmap=0.0.0.0/0:$myip --enet-smac=$mymac --ttl=5
    tcprewrite --infile=/tmp/temp1.pcap --outfile=/tmp/final.pcap --fixcsum
    tcpreplay --loop=0 --intf1=$myif /tmp/final.pcap &
fi