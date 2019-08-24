#! /bin/bash


key="${1}"
case ${key} in
start)
	source ../../demo-openrc.sh
	echo "	Starting gateway vms."
        openstack server list -c ID -c Name | grep gateway | awk '{print $2}' | xargs -I {} openstack server start {}
	;;
stop)
	source ../../demo-openrc.sh
	echo "	Stopping gateway vms."
        openstack server list -c ID -c Name | grep gateway | awk '{print $2}' | xargs -I {} openstack server stop {}
        ;;
create)
	if [ $# -lt 2 ]
	then
        	echo "$0 <create> <count>"
        	exit
	fi

	echo "Checking network existence."
	source ../../demo-openrc.sh
	openstack port list -c Name | grep gateway;
        if test $? -eq 0; 
	then
		echo "	Creating gateway vms."
		INPUTPARAM="${2}"
		counter=1
		while [ $counter -le $INPUTPARAM ];do
			name=gateway_$counter
			echo "	Creating instance named: $name."
			openstack server create --flavor ds512M --image Gateway --port port_out_$name --port port_$name --key-name rps --wait $name > /dev/null
			((counter++))
		done
	else
		echo "Port and networks are not created. Use networks.sh."
                exit
	fi
        ;;

delete)
	source ../../demo-openrc.sh
	echo "	Deleting gateway vms."
	openstack server list -c ID -c Name | grep gateway | awk '{print $2}' | xargs -I {} openstack server delete {}
        ;;
status)
        source ../../demo-openrc.sh
        echo "  Status of gateway vms."
        openstack server list -c Name -c Status | grep 'gateway' 
        ;;
*)    # unknown option
        echo "Unknown option."
	echo "$0 <create> <gateway count>"
	echo "$0 <delete/start/stop/status>"
        ;;
esac
