#! /bin/bash
ps ax | grep "tcpreplay" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    file=/opt/data/`shuf -i 1-10 -n 1`.pcapng
    myif=`netstat -i | grep ens | awk '{ print $1 }'`
    myip=`ip a | grep $myif | grep inet | awk '{ print $2 }' | cut -d "/" -f 1`
    mymac=`ip a | grep -A 1 "$myif\:"   | grep ether | awk '{ print $2 }'`
    /usr/bin/tcprewrite --infile=/tmp/data.pcapng --outfile=/tmp/temp1.pcap --srcipmap=0.0.0.0/0:$myip --enet-smac=$mymac --ttl=5
    /usr/bin/tcprewrite --infile=/tmp/temp1.pcap --outfile=/tmp/final.pcap --fixcsum
    /usr/bin/tcpreplay --loop=0 --intf1=$myif /tmp/final.pcap &
fi