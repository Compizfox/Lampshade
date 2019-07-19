#!/bin/bash
#SBATCH -t 24:00:00
#SBATCH -n 24
#SBATCH --mail-type=ALL
#SBATCH --mail-user=lars@tuxplace.nl

# Call like this:
#sbatch --array=0-5%2 rcb_job.sh

module load python/3.6-intel-2018-u2
module load mpi/impi
module load foss/2018b

srun python3 run_rcb_MPI.py
