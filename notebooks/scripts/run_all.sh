#### This is meant only for older definition of ground truth.
####

#./expanded_match_without_subnetting_t1.sh Simple_PatternSearcher_MFI_FPMax >> /home/rhishi/Documents/tmp/submission/timestep/out/Simple_PatternSearcher_MFI_FPMax.dat
#./expanded_match_with_subnetting_t1.sh Simple_PatternSearcher_MFI_FPMax_Subnet >> /home/rhishi/Documents/tmp/submission/timestep/out/Simple_PatternSearcher_MFI_FPMax_Subnet.dat

#./expanded_match_without_subnetting_t1.sh BackwardLooking_PatternSearcher_MFI_FPMax >> /home/rhishi/Documents/tmp/submission/timestep/out/BackwardLooking_PatternSearcher_MFI_FPMax.dat
#./expanded_match_with_subnetting_t1.sh BackwardLooking_PatternSearcher_MFI_FPMax_Subnet >> /home/rhishi/Documents/tmp/submission/timestep/out/BackwardLooking_PatternSearcher_MFI_FPMax_Subnet.dat

alg="ConstantSup_PatternSearcher_MFI_FPMax_Subnet"
ofile=/home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
if test -f "$ofile"; then
    rm /home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
fi
./expanded_match_with_subnetting_t1.sh "$alg" >> $ofile

alg="Simple_PatternSearcher_MFI_FPMax_Subnet"
ofile=/home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
if test -f "$ofile"; then
    rm /home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
fi
./expanded_match_with_subnetting_t1.sh "$alg" >> $ofile

alg="BackwardLooking_Tw_1_PatternSearcher_MFI_FPMax_Subnet"
ofile=/home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
if test -f "$ofile"; then
    rm /home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
fi
./expanded_match_with_subnetting_t1.sh "$alg" >> $ofile

alg="BackwardLooking_Tw_3_PatternSearcher_MFI_FPMax_Subnet"
ofile=/home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
if test -f "$ofile"; then
    rm /home/rhishi/Documents/tmp/submission/timestep/out/"$alg".dat
fi
./expanded_match_with_subnetting_t1.sh "$alg" >> $ofile