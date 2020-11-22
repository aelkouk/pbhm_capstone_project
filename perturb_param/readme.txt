Example of preparation required for Loobos site:
- Move this folder 'perturb_param' into pbhmCourse_student/2_process_based_modelling
- Fix paths in summa_zFileManager_Loobos.txt to match your current path
- Reduce the simulation period in summa_zFileManager_Loobos.txt to 2 years
- Keep 'mLayerVolFracLiq' and 'averageRoutedRunoff' lines in 'summa_zModelOutput.txt' and remove the rest
- If do not exist, create the SUMMA output directory 2_process_based_modelling/output/plumber/Loobos
- Sbatch jobs.sh 'sbatch --array=1-6 jobs.sh'






