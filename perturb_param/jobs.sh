#!/bin/bash

#SBATCH --job-name=test
#SBATCH --ntasks=1
#SBATCH --time=0-01:59:00

# load the matlab module for running the 'change_param.m' function
module load matlab/2020a

# define paths
base_path=${HOME}/pbhmCourse_student/2_process_based_modelling
site_path=${base_path}/settings/plumber/Loobos                             
summa_settings=${site_path}/summa_zFileManager_Loobos.txt
SOILPARM_file=${site_path}/SOILPARM.TBL
sobol_file=${base_path}/perturb_param/SobolPAR_Matrix/SobolPAR_MatrixA.csv # Change to desired file
summa_exe=${base_path}/perturb_param/summa.exe
log_file=${base_path}/perturb_param/log_summa.txt

for row in {1..100}; do
        # Run script chnage SOILTBL using $row value in SobolPAR_Matrix.csv file
        # Script takes as input: $SOILPARM_file, $SobolMatrix, $row,
        # Change the name of the table
        mv $SOILPARM_file ${site_path}/"SOILPARM_or.TBL"
        # matlab code 2
        matlab -batch "change_param_all($row,'$sobol_file','$SOILPARM_file')"
        # Run summa with $row as output suffix
        summa_command="$summa_exe -m $summa_settings --suffix $row"

        # Run as [SUMMA call] > [log file path]
	$summa_command >> $log_file
done
