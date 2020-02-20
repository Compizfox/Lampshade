#!/usr/bin/env python3

"""
Runs one simulation with the given parameters.
"""

from datetime import datetime
from os import path
from subprocess import run
import argparse

import psutil

from Simulation import Simulation

if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("-var", "--variable", default={}, type=lambda s:
	                    {k: float(v) for k, v in [var.split('=') for var in s.split(' ')]},
	                    help="Arbitrary equal-style variable(s) to set. Multiple variables should be separated by "
	                         "spaces. Values should be floats. Example: -var mu=1.0 cps=1.0",
	                    metavar="VAR=VALUE")
	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp',
						help="Path to the LAMMPS binary. May be a command, like \"mpirun lmp\"")
	args = parser.parse_args()

	print(args.variable)

	cpu_count = psutil.cpu_count(logical=False)
	if args.lammps_path == 'lmp':
		args.lammps_path = 'mpirun -np {} lmp -sf omp -pk omp 1'.format(cpu_count)

	# Run equilibration if equilibrated data file is not found
	if not path.isfile('data.equi'):
		# Get first values of vars
		sim = Simulation(args.lammps_path, args.dry_run)
		sim.run_equi(args.variable)

	sim = Simulation(args.lammps_path, args.dry_run)
	sim.sample_coord(args.variable)
