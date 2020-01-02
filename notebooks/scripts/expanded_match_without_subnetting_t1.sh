#! /bin/bash

# with support values 2-100
# for i in `seq 2 2 100`;do ./*.sh $i >> fixed_ip.txt;done

# Argument1 -> support value

# It is assumed that FIM patterns are in src/data_mask_$2 location

algo=$1


create_files () {
#echo "Running for $algo"
  infile=/home/rhishi/Documents/tmp/submission/timestep/"$algo"/"$step"
  outfile=/home/rhishi/Documents/tmp/submission/timestep/out/"$algo"_step_"$step"_found.txt
  gtfile=/home/rhishi/Documents/tmp/submission/timestep/out/"$algo"_step_"$step"_gt.txt
  nffile=/home/rhishi/Documents/tmp/submission/timestep/out/"$algo"_step_"$step"_nf.txt

  echo > $outfile
  if test -f $gtfile; then
    rm $gtfile
  fi

  if test -f $nffile; then
    rm $nffile
  fi
}

check_scanouts () {

  echo "iot --------------------- outgoing scans" >> $outfile

  # outgoing scans
  for ip in "$@";
  do
    pattern_1=""$ip",.*,.*,6\.22,.*"
    grep -r -e "$pattern_1" $infile | grep "dir_0"  >> $outfile
    out=`grep -r -e "$pattern_1" $infile | grep "dir_0" | wc -l` 
    if test $out -eq 0; then
      echo 0 "$pattern_1" >> $nffile
    fi
    echo 0 "$pattern_1" >> $gtfile
  done

  echo "iot --------------------- iots incoming scans" >> $outfile

  # incomings for same
  for ip in "$@"; 
  do
    pattern_1=".*,"$ip",.*,6\.22,.*"
    grep -r -e "$pattern_1" $infile | grep "dir_1" >> $outfile
    out=`grep -r -e "$pattern_1" $infile | grep "dir_1" | wc -l` 
    if test $out -eq 0; then
      echo 1 "$pattern_1" >> $nffile
    fi
    echo 1 "$pattern_1" >> $gtfile
  done
}

check_scans_and_logins () {
  echo "iot --------------------- scan attempts bot1" >> $outfile
  # Bot1 scan and login attempts
  retip="192.168.1.6"

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
  retip="192.168.1.41"

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
}

check_loader () {
  echo "iot --------------------- loader" >> $outfile
  # Loader
  retip="199.198.197.196"

  # expand iot
  loader_exact=".*,"$retip",.*,6\.8000,L"
  grep -r -e "$loader_exact" $infile >> $outfile
  out=`grep -r -e "$loader_exact" $infile | wc -l`
  if test $out -eq 0; then
      echo 0 "$loader_exact" >> $nffile
  fi
  echo 0 "$loader_exact" >> $gtfile
}

check_cnc () {
  echo "iot --------------------- c&c" >> $outfile
  # C&C
  retip="199.198.197.196"
  cnc_exact=".*,"$retip",.*,6\.4567,*"
  grep -r -e "$cnc_exact" $infile >> $outfile
  out=`grep -r -e "$cnc_exact" $infile | wc -l`
  if test $out -eq 0; then
      echo 0 "$cnc_exact" >> $nffile
  fi
  echo 0 "$cnc_exact" >> $gtfile
  
  #cnc_failed=".*,"$retip",.*,6\.4567,S"
  #grep -r -e "$cnc_failed" $infile >> $outfile
  #out=`grep -r -e "$cnc_failed" $infile | wc -l`
  #if test $out -eq 0; then
  #    echo 0 "$cnc_failed" >> $nffile
  #fi
  #echo 0 "$cnc_failed" >> $gtfile
}

check_ddos () {
  echo "iot --------------------- ddos" >> $outfile
  # http ddos
  retip="137.136.135.134"

  # expand iot
  ddos_exact=".*,"$retip",.*,6\.80,M"
  grep -r -e "$ddos_exact" $infile >> $outfile
  out=`grep -r -e "$ddos_exact" $infile | wc -l`
  if test $out -eq 0; then
      echo 0 "$ddos_exact" >> $nffile
  fi
  echo 0 "$ddos_exact" >> $gtfile
}

check_rddos () {
  echo "iot --------------------- rddos" >> $outfile
  # reflective ddos
  ip1="137.136.135.134"
  retip="9.9.9.9"
  #echo $retip, $ip1
  rddos_exact=""$ip1","$retip",.*,17\.53,S"
  grep -r -e "$rddos_exact" $infile >> $outfile
  out=`grep -r -e "$rddos_exact" $infile | wc -l`
  if test $out -eq 0; then
      echo 0 "$rddos_exact" >> $nffile
  fi
  echo 0 "$rddos_exact" >> $gtfile
}

calculate_all () {
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
  echo $step $total $uevents $gtevent $notfound $precision $recall
}

# Time step 0
step=0
create_files
check_scans_and_logins
calculate_all

# Time step 1
step=1
create_files
check_scans_and_logins
check_loader
calculate_all

# Time step 2
step=2
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.9 172.16.4.10 172.16.5.10 172.16.7.10
calculate_all

# Time step 3
step=3
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.9 172.16.3.14 172.16.4.10 172.16.4.13 172.16.4.7 172.16.5.10 172.16.6.12 172.16.7.10
calculate_all

# Time step 4
step=4
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.11 172.16.1.9 172.16.2.6 172.16.3.14 172.16.4.10 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.12 172.16.5.13 172.16.6.11 172.16.6.12 172.16.6.14 172.16.7.10 172.16.7.11 172.16.7.13
calculate_all

# Time step 5
step=5
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.4 172.16.6.11 172.16.6.12 172.16.6.14 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13
check_ddos
calculate_all

# Time step 6
step=6
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.10 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.2.8 172.16.3.12 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.12 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.4 172.16.6.11 172.16.6.12 172.16.6.14 172.16.6.3 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13 172.16.7.9
calculate_all

# Time step 7
step=7
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.10 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.2.8 172.16.3.12 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.12 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.14 172.16.5.4 172.16.6.10 172.16.6.11 172.16.6.12 172.16.6.14 172.16.6.3 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13 172.16.7.9
check_rddos
calculate_all

# Time step 8
step=8
create_files
check_scans_and_logins
check_loader
check_cnc
check_scanouts 172.16.1.10 172.16.1.11 172.16.1.14 172.16.1.9 172.16.2.3 172.16.2.6 172.16.2.8 172.16.3.12 172.16.3.14 172.16.3.7 172.16.4.10 172.16.4.12 172.16.4.13 172.16.4.7 172.16.4.8 172.16.5.10 172.16.5.11 172.16.5.12 172.16.5.13 172.16.5.14 172.16.5.4 172.16.6.10 172.16.6.11 172.16.6.12 172.16.6.14 172.16.6.3 172.16.7.10 172.16.7.11 172.16.7.12 172.16.7.13 172.16.7.9
calculate_all