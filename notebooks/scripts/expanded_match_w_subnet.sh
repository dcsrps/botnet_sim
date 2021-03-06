#! /bin/bash
path=$1
support=$2
#echo "Running for $algo"
algo=`echo $path | tr "/" "\t" | awk {' print $NF'}`

infile="$path"/support_"$support"
outfile=/tmp/"$algo"_found_"$support".txt
gtfile=/tmp/"$algo"_gt.txt
nffile=/tmp/"$algo"_nf.txt

echo > $outfile
if test -f $gtfile; then
  rm $gtfile
fi

if test -f $nffile; then
  rm $nffile
fi

subnet=16

get_masked_ip () {
  IFS=. read -r i1 i2 i3 i4 <<< "$1"
  IFS=. read -r m1 m2 m3 m4 <<< "$NETMASK"
  #echo "%d.%d.%d.%d\n" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))"
  retip="$((i1 & m1))"."$((i2 & m2))"."$((i3 & m3))"."$((i4 & m4))"
}

value=$(( 0xffffffff ^ ((1 << (32 - $subnet)) - 1) ))
NETMASK="$(( (value >> 24) & 0xff )).$(( (value >> 16) & 0xff )).$(( (value >> 8) & 0xff )).$(( value & 0xff ))"


echo "iot --------------------- outgoing scans" >> $outfile

# outgoing scans
for ip in 172.16.1.10 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.2.8 172.16.3.12 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.12 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.14 172.16.5.4 172.16.6.10 172.16.6.11 172.16.6.12 172.16.6.14 172.16.6.3 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13 172.16.7.9; do
  get_masked_ip "$ip"
  pattern_1=""$retip",.*,.*,6\.22,.*"
  grep -r -e "$pattern_1" $infile | grep "dir_0"  >> $outfile
  out=`grep -r -e "$pattern_1" $infile | grep "dir_0" | wc -l` 
  if test $out -eq 0; then
    echo 0 "$pattern_1" >> $nffile
  fi
  echo 0 "$pattern_1" >> $gtfile
done

echo "iot --------------------- iots incoming scans" >> $outfile

# incomings for same
for ip in 172.16.1.10 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.2.8 172.16.3.12 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.14 172.16.5.4 172.16.6.10 172.16.6.11 172.16.6.12 172.16.6.14 172.16.6.3 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13 172.16.7.9; do
  get_masked_ip "$ip"
  pattern_1=".*,"$retip",.*,6\.22,.*"
  grep -r -e "$pattern_1" $infile | grep "dir_1" >> $outfile
  out=`grep -r -e "$pattern_1" $infile | grep "dir_1" | wc -l` 
  if test $out -eq 0; then
    echo 1 "$pattern_1" >> $nffile
  fi
  echo 1 "$pattern_1" >> $gtfile
done

echo "iot --------------------- scan attempts bot1" >> $outfile
# Bot1 scan and login attempts
get_masked_ip "192.168.1.6"

#exact match
bot1scan_exact=".*,"$retip",.*,6\.22,S"
grep -r -e "$bot1scan_exact" $infile >> $outfile
out=`grep -r -e "$bot1scan_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 1 "$bot1scan_exact" >> $nffile
fi
echo 1 "$bot1scan_exact" >> $gtfile

echo "iot --------------------- login attempts bot1" >> $outfile

# exact match
bot1login_exact=".*,"$retip",.*,6\.22,M"
grep -r -e "$bot1login_exact" $infile >> $outfile
out=`grep -r -e "$bot1login_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 1 "$bot1login_exact" >> $nffile
fi
echo 1 "$bot1login_exact" >> $gtfile

echo "iot --------------------- scan attempts bot2" >> $outfile
# Bot2 scan and login attempts
get_masked_ip "192.168.1.41"

# expand iot
bot2scan_exact=".*,"$retip",.*,6\.22,S"
grep -r -e "$bot2scan_exact" $infile  >> $outfile
out=`grep -r -e "$bot2scan_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 1 "$bot2scan_exact" >> $nffile
fi
echo 1 "$bot2scan_exact" >> $gtfile

echo "iot --------------------- login attempts bot2" >> $outfile
# expand iot
bot2login_exact=".*,"$retip",.*,6\.22,M"
grep -r -e "$bot2login_exact" $infile >> $outfile
out=`grep -r -e "$bot2login_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 1 "$bot2login_exact" >> $nffile
fi
echo 1 "$bot2login_exact" >> $gtfile

echo "iot --------------------- loader" >> $outfile
# Loader
get_masked_ip "199.198.197.196"

# expand iot
loader_exact=".*,"$retip",.*,6\.8000,L"
grep -r -e "$loader_exact" $infile >> $outfile
out=`grep -r -e "$loader_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 0 "$loader_exact" >> $nffile
fi
echo 0 "$loader_exact" >> $gtfile

echo "iot --------------------- c&c" >> $outfile
# C&C
cnc_exact=".*,"$retip",.*,6\.4567,.*"
grep -r -e "$cnc_exact" $infile >> $outfile
out=`grep -r -e "$cnc_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 0 "$cnc_exact" >> $nffile
fi
echo 0 "$cnc_exact" >> $gtfile

echo "iot --------------------- ddos" >> $outfile
# http ddos
get_masked_ip "137.136.135.134"

# expand iot
ddos_exact=".*,"$retip",.*,6\.80,M"
grep -r -e "$ddos_exact" $infile >> $outfile
out=`grep -r -e "$ddos_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 0 "$ddos_exact" >> $nffile
fi
echo 0 "$ddos_exact" >> $gtfile

echo "iot --------------------- rddos" >> $outfile
# reflective ddos
ip1=$retip
get_masked_ip "9.9.9.9"
#echo $retip, $ip1
rddos_exact=""$ip1","$retip",.*,17\.53,S"
grep -r -e "$rddos_exact" $infile >> $outfile
out=`grep -r -e "$rddos_exact" $infile | wc -l`
if test $out -eq 0; then
    echo 0 "$rddos_exact" >> $nffile
fi
echo 0 "$rddos_exact" >> $gtfile

# commented these to seggregate input and output events. As we have only two files.
#uevents=`grep -v -e "iot" -e ^$  $outfile  | cut -d ":" -f 2 | sort  -u | wc -l`
uevents=`grep -v -e "iot" -e ^$  $outfile | sort  -u | wc -l`
total=`grep -r -v "iot" $infile | wc -l | awk '{ print $1 }'`
gtevent=`sort -u $gtfile  | wc -l`
notfound=0
if test -f $nffile; then
    notfound=`sort -u $nffile  | wc -l`
fi
precision=`echo "scale=4; $uevents/$total" | bc`
recall=`echo "scale=4; ($gtevent-$notfound)/$gtevent" | bc`
echo $support $total $uevents $gtevent $notfound $precision $recall

