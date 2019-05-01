#!/bin/bash
RUN_FILE=`pwd`/mtd.$$
MYDIR=`pwd`
echo "#!/bin/sh" >> $RUN_FILE
echo "#PBS -l walltime=23:59:00" >> $RUN_FILE
echo "#PBS -l select=1:ncpus=16" >> $RUN_FILE
echo "mkdir /scratch/\$USER/\$PBS_JOBID" >> $RUN_FILE
echo "trap 'rm -r /scratch/\$USER/\$PBS_JOBID' TERM EXIT" >> $RUN_FILE
echo "cp -r /arabica/$MYDIR/* /scratch/\$USER/\$PBS_JOBID/ || exit 1" >> $RUN_FILE
echo "cd /scratch/\$USER/\$PBS_JOBID || exit 2 " >> $RUN_FILE
echo "export OMP_NUM_THREADS=1" >> $RUN_FILE
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib/" >> $RUN_FILE
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/software/plumed/plumed250/lib" >> $RUN_FILE
for i in `seq 0 31`;
do
echo "/software/plumed/gromacs20185plumed250/bin/gmx_mpi grompp -f md_$i.mdp -c mtd0_$i.gro -t mtd0_$i.cpt -p topol.top -o mtd1_$i.tpr" >> $RUN_FILE
echo "rm mdout.mdp" >> $RUN_FILE
done
echo "/software/mpi/openmpi400/bin/mpirun -np 32 --hostfile hostfile /software/plumed/gromacs20185plumed250/bin/gmx_mpi mdrun -deffnm mtd1_ -plumed plumed.dat -multi 32 -replex 500" >> $RUN_FILE
echo "cp -r * /arabica/$MYDIR/ || {  trap - TERM EXIT && echo \"problem happened\" >&2 ; exit 1 ;}" >> $RUN_FILE
qsub $RUN_FILE

