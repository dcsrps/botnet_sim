#! /bin/bash
ps ax | grep "gateway.py" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/gateway/gateway.py > /tmp/gateway.py
    export -p PATH=$PATH:/usr/sbin/
    if=`netstat -ai | grep ens | awk 'NR==2 {print $1}'`
    octet3=`ip a | grep "inet.*ens3" | awk '{print $2}' | cut -d "." -f 4 | cut -d "/" -f 1`
    id=$((octet3-50))
    ip=172.16.$id.1
    /sbin/ifconfig $if $ip/24 up
    counter=1
    while [ $counter -le 10 ];do
        let a=50+$counter
        if test $counter -eq $((octet3-50)); then
            /sbin/route del -net 172.16.$counter.0/24 gw 192.168.1.$a
        fi        
        ((counter++))
    done
    python3 /tmp/gateway.py 172.16.131.64 $if $ip/24 $id &
fi
