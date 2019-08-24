#! /bin/bash


key="${1}"
case ${key} in
create)
	source ../../demo-openrc.sh
        INPUTPARAM="${2}"
	counter=1
	while [ $counter -le $INPUTPARAM ];do
		name=gateway_$counter
		echo "	Creating network: $name." 
		let a=50+$counter
		openstack network create $name > /dev/null 
		openstack subnet create --network $name --subnet-range 172.16.$counter.1/28 --gateway 172.16.$counter.1 subnet_$name > /dev/null
		openstack port create --network $name --fixed-ip ip-address=172.16.$counter.1 --disable-port-security port_$name > /dev/null
		openstack port create --network out --fixed-ip ip-address=192.168.1.$a --disable-port-security port_out_$name > /dev/null
		((counter++))
	done
        ;;
delete)
	source ../../demo-openrc.sh
	echo "	Deleting ports and networks."
	openstack port list -c Name | grep gateway | awk '{print $2}' | xargs -I {} openstack port delete {}
        openstack network list -c Name | grep gateway | awk '{print $2}' | xargs -I {} openstack network delete {}	
        ;;
*)    # unknown option
        echo "Unknown option."
	echo "network <create> <count>"
	echo "network <delete>"
        ;;
esac
