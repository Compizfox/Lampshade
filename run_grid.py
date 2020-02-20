#!/usr/bin/env python3

"""
Samples a mesh grid in the 2D EPP-EPS parameter space.
No script-level MPI; different points are simulated in parallel using Python multiprocessing.

Runs a (single, common) equilibration if equilibrated data file is not found with n-rank MPI where n is the number of
cores in the system.

By default, calls LAMMPS with 1x OMP and auto-calculated MPI ranks to saturate the cores in te system.

Requires psutil.
"""

from multiprocessing import Pool, current_process, cpu_count
from itertools import product
from os import path
from math import floor
import argparse

import psutil

from Simulation import Simulation


# We use a function with a global var here over a closure in __main__ because non-module-level functions are not
# callable by Pool.starmap for some reason
def start_sim(*vars_values: float) -> None:
	"""
	Start the simulation by creating a Simulation and running it
	:param float *vars_values: Custom variable values
	"""
	# Reconstruct vars dict
	vars = {k: v for k, v in zip(args.variable.keys(), vars_values)}

	sim = Simulation(args.lammps_path, args.dry_run, current_process().name)
	sim.sample_coord(vars)


def init_pool(args_dict: dict) -> None:
	"""
	Initialise workers with arguments dict as global args
	:param dict args_dict: Arguments
	"""
	global args
	args = args_dict


if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Create dict of lists from argument string where several variables are separated by spaces, variable names and
	# their values are separated by =, and values are a comma-separated list
	parser.add_argument("-var", "--variable", default={}, type=lambda s:
	                    {k: [float(i) for i in v.split(',')] for k, v in [var.split('=') for var in s.split(' ')]},
	                    # ^ *Sometimes my genius is... it's almost frightening.*
	                    help="Arbitrary equal-style variable(s) to set. Can be arrays, with values separated by "
	                         "commas. In this case, a simulation will be run for every combination of values."
	                         "Multiple variables should be separated by spaces. Values should be floats. Example: -var "
	                         "mu=1.0,2.0 cps=1.5,2.0",
	                    metavar="VAR=VALUE")

	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp',
	                    help="Path to the LAMMPS binary. May be a command, like \"mpirun lmp\"")
	args = parser.parse_args()

	# Create cartesian product of parameters. Returns list of tuples (*vars)
	coordList = list(product(*args.variable.values()))

	cpu_count = psutil.cpu_count(logical=False)

	print("Got {} jobs, distributed over {} workers:".format(len(coordList), cpu_count))
	print(*coordList, sep="\n")

	# Run equilibration if equilibrated data file is not found
	if not path.isfile('data.equi'):
		if args.lammps_path == 'lmp':
			args.lammps_path = 'mpirun -np {} lmp -sf omp -pk omp 1'.format(cpu_count)

		# Get first values of vars
		first_vars = {k: v[0] for k, v in args.variable.items()}

		sim = Simulation(args.lammps_path, args.dry_run)
		sim.run_equi(first_vars)

	if args.lammps_path == 'lmp':
		mpi_ranks = floor(cpu_count / len(coordList))
		args.lammps_path = 'mpirun --bind-to socket -np {} lmp -sf omp -pk omp 1'.format(mpi_ranks)

	# Create pool of number of cores workers
	with Pool(cpu_count, initializer=init_pool, initargs=(args,)) as p:
		p.starmap(start_sim, coordList)
