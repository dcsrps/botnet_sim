#!/bin/bash


#No of Gateways, min and max iot devices per gateway
gw_count=2
min_iot=2
max_iot=3

manager_install_script=../install/manager
gateway_install_script=../install/gateway
host_install_script=../install/host
iot_install_script=../install/iot
#botnet_install_script=
cnc_install_script=../install/cnc
#scanner_install_script=
#dns_install_script=
#victim_install_script=

base_image=ubuntu18
key_name=iot_rhishi

source ../../demo-openrc.sh

instance_count=0
port_count=0
route_count=0
declare -A instance_array
declare -A port_array
declare -A route_array


create_network () {
	echo "	Creating network: $1" 
	openstack network create $1 > /dev/null 
	openstack subnet create --network $1 --subnet-range $2 --gateway $3 --allocation-pool start=$4,end=$5 subnet_$1 > /dev/null
}

create_port () {
	openstack port create --network $1 --fixed-ip ip-address=$2 --disable-port-security $3 > /dev/null
	if [ $? -eq 0 ]
	then
  		echo "	Successfully created port $3."
		port_array[$port_count]=$3
		((++port_count))
	else
  		echo "	ERROR: Could not create port." >&2
	fi
}

create_instance_with_port () {
	echo " Creating instance named: $3"
	openstack server create --flavor ds512M --image $1 --nic port-id=$2 --user-data $4 --key-name $key_name $3 > /dev/null
	instance_array[$instance_count]=$3
        ((++instance_count))
}

create_instance_with_network () {
	echo " Creating instance named: $3"
	openstack server create --flavor ds512M --image $1 --network $2 --user-data $4 --key-name $key_name $3 > /dev/null
	instance_array[$instance_count]=$3
        ((++instance_count))
}

create_gateway_instance () {
	echo " Creating instance named: $4"
	openstack server create --flavor ds512M --image $1 --port $2  --port $3 --user-data $5 --key-name $key_name --wait $4 > /dev/null
        instance_array[$instance_count]=$4
        ((++instance_count))

	#local temp_str=`openstack server show $4 | grep addresses`
	#out_ip=`echo $temp_str | sed -e 's/.*out=\(.*\);.*/\1/'`
	#intNet_ip=`echo $temp_str | sed -e "s/.*$2=\(.*\).*|/\1/"`
}


add_iot_devices () {
	local iots=0
	iots=`shuf -i $min_iot-$max_iot -n 1`

	echo " Adding $iots in network: $1."

	local count=1
	while [ $count -le $iots ];do
		create_instance_with_network $base_image $1 $2$count $3
		((++count))
	done	
}


delete_all () {
	local count=0
	for i in "${instance_array[@]}"; do 
		echo "	Deleting instance $i"
		openstack server delete $i
		unset instance_array[$count]
		((++count))
	done

	count=0
	for i in "${route_array[@]}"; do
                echo "	Deleting route $i"
                openstack subnet unset --host-route $i
                unset route_array[$count]
                ((++count))
        done


	count=0
	for i in "${port_array[@]}"; do 
		echo "	Deleting port $i"
		openstack port delete $i
		unset port_array[$count]
		((++count))
	done

	count=1
	while [ $count -le $gw_count ];do
		echo "	Deleting network gateway_$count"
		openstack network delete gateway_$count
		((++count))
	done

	rm $tmp_gw $tmp_host $tmp_manager
}

tmp_gw="$gateway_install_script"_tmp
tmp_host="$host_install_script"_tmp
tmp_manager="$manager_install_script"_tmp

cp $gateway_install_script $tmp_gw
cp $host_install_script $tmp_host

echo "Step 1. Creating Networks."
echo "----------------------------"

counter=1
while [ $counter -le $gw_count ];do
	create_network gateway_$counter 172.16.$counter.0/24 172.16.$counter.1 172.16.$counter.2 172.16.$counter.50
	create_port gateway_$counter 172.16.$counter.1 port_gateway_$counter 
        
	let a=50+$counter
	create_port out 192.168.1.$a port_out_$counter

	echo route add -net 172.16.$counter.0/24 gw 192.168.1.$a >> $tmp_gw
	echo route add -net 172.16.$counter.0/24 gw 192.168.1.$a >> $tmp_host
	((counter++))

done
echo >> $tmp_host

cat $tmp_host >> $tmp_manager

echo "----------------------------"
echo "Step 2. Adding Manager and C&C."
echo "----------------------------"
create_instance_with_network $base_image out manager $manager_install_script
#create_instance_with_network $base_image out cnc $cnc_install_script

servers=`openstack server list`
manager_ip=`echo $servers | grep manager | awk '{ print $8 }' | cut -d "=" -f 2`
#cnc_ip=`echo $servers | grep cnc | awk '{ print $8 }' | cut -d "=" -f 2`

echo "----------------------------"
echo "Step 3. Creating Gateways."
echo "----------------------------"
counter=1
while [ $counter -le $gw_count ];do
	cp $tmp_gw /tmp/gateway_$counter.sh
	sed -i -e "s|IP|172.16.$counter.1|g" -e "/172.16.$counter.0/d" -e "s|MANAGER|$manager_ip|"  /tmp/gateway_$counter.sh
	echo  >> /tmp/gateway_$counter.sh
	create_gateway_instance $base_image port_out_$counter port_gateway_$counter gateway_instance_$counter /tmp/gateway_$counter.sh
	((counter++))
done

echo "----------------------------"
echo "Step 4. Adding IoT devices."
echo "----------------------------"
counter=1
while [ $counter -le $gw_count ];do	
	add_iot_devices gateway_$counter iot_$counter $iot_install_script	
	((counter++))
done


echo "----------------------------"
echo "Step 5. Starting Packet Capture."
echo "----------------------------"
portids=`openstack port list`
counter=1
while [ $counter -le $gw_count ];do
	local tcpif=`echo $portids | grep port_gateway_$counter | awk '{ print substr($2,1,11) }'`
	sudo ovs-tcpdump -i tap$tapif -w /tmp/gateway_$counter.pcap &
        ((counter++))
done


echo "----------------------------"
echo "Step 6. Creating IoT servers."
echo "----------------------------"

echo "----------------------------"
echo "Step 7. Creating Scanner and Botnet."
echo "----------------------------"


read -rsn1 -p"Press any key to close all '-->";echo
delete_all

echo All done

#openstack network create out
#openstack subnet create extSubnet --network out --subnet-range 10.0.0.0/24

# Create router for outer communication
#openstack router create extRouter

#openstack router set ROUTER --external-gateway NETWORK
#openstack router add subnet ROUTER SUBNET
