export OMP_NUM_THREADS=1
gmx_mpi grompp -f mtd -c after_em -p molecule_gmx.top -o mtd1
mpirun -np 1 gmx_mpi mdrun -deffnm mtd1 -plumed plumed.dat

