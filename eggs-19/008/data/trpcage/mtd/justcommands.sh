export OMP_NUM_THREADS=1
gmx_mpi grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o mtd1.tpr
mpirun -np 8 gmx_mpi mdrun -deffnm mtd1 -plumed plumed.dat

