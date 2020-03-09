#!/bin/bash
#SBATCH -t 24:00:00
#SBATCH -n 24
#SBATCH --mail-type=ALL
#SBATCH --mail-user=l.b.veldscholte@utwente.nl

# Call like this:
#sbatch --array=0-5%2 rcb_job.sh

module load 2019
module load Python/3.7.5-foss-2018b

python3 run_sbatch.py
