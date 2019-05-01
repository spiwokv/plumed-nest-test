#!/bin/bash
RUN_FILE=`pwd`/mtd.$$
MYDIR=`pwd`
echo "#!/bin/sh" >> $RUN_FILE
echo "#PBS -l walltime=23:59:00" >> $RUN_FILE
echo "#PBS -l select=1:ncpus=1" >> $RUN_FILE
echo "mkdir /scratch/\$USER/\$PBS_JOBID" >> $RUN_FILE
echo "trap 'rm -r /scratch/\$USER/\$PBS_JOBID' TERM EXIT" >> $RUN_FILE
echo "cp -r /arabica/$MYDIR/* /scratch/\$USER/\$PBS_JOBID/ || exit 1" >> $RUN_FILE
echo "cd /scratch/\$USER/\$PBS_JOBID || exit 2 " >> $RUN_FILE
echo "export OMP_NUM_THREADS=1" >> $RUN_FILE
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib/" >> $RUN_FILE
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/software/plumed/plumed250/lib" >> $RUN_FILE
echo "/software/plumed/gromacs20185plumed250/bin/gmx_mpi grompp -f mtd -c after_em -p molecule_gmx.top -o mtd1" >> $RUN_FILE
echo "/software/mpi/openmpi400/bin/mpirun -np 1 /software/plumed/gromacs20185plumed250/bin/gmx_mpi mdrun -deffnm mtd1 -plumed plumed.dat" >> $RUN_FILE
echo "cp -r * /arabica/$MYDIR/ || {  trap - TERM EXIT && echo \"problem happened\" >&2 ; exit 1 ;}" >> $RUN_FILE
qsub $RUN_FILE

