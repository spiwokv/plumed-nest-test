export OMP_NUM_THREADS=1
for i in `seq 0 19`;
do
gmx_mpi grompp -f fg -c frame$i -p AceAlaNme -o mtd1_$i -maxwarn 666
rm mdout.mdp
done
mpirun -np 20 gmx_mpi mdrun -s mtd1_ -o mtd1_ -e mtd1_ -g mtd1_ -c after_mtd1_ -plumed plumed -multi 20

