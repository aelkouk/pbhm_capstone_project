#!/bin/bash


#SBATCH --job-name=test
#SBATCH --ntasks=1
#SBATCH --time=0-00:20:00



base_path=${HOME}/pbhmCourse_student/2_process_based_modelling
summa_settings=${base_path}/settings/plumber/Loobos/summa_zFileManager_Loobos.txt
SOILTBL_file=${base_path}/settings/plumber/Loobos/SOILPARM.TBL
SobolMatrix=${base_path}/SobolPAR_MatrixA.csv
summa_exe=${base_path}/summa.exe
log_file=${base_path}/log_summa.txt

for row in {1..100}; do
	# Run script chnage SOILTBL using $row value in SobolPAR_Matrix.csv file
	# Script takes as input: $SOILTBL_file, $SobolMatrix, $row, 

	# Run summa with $row as output suffix	
	summa_command="$summa_exe -m $summa_settings --suffix $row"

	# Run as [SUMMA call] > [log file path]
	$summa_command >> $log_file
done



































