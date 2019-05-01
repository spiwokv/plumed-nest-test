export OMP_NUM_THREADS=1
for i in `seq 0 31`;
do
grompp -f md_$i.mdp -c mtd0_$i.gro -t mtd0_$i.cpt -p topol.top -o mtd1_$i.tpr
rm mdout.mdp
done
mpirun -np 32 gmx_mpi mdrun -deffnm mtd1_ -plumed plumed.dat -multi 32 -replex 500

