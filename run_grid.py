#!/usr/bin/env python3

"""
Samples a mesh grid in the 2D EPP-EPS parameter space.
No MPI; different points are simulated in parallel using Python multiprocessing.

Call with double dash to specify negative values for the required positional arguments, for example:
run_grid.py -- 1.0 1.0 -3.5,-3.0
"""

from multiprocessing import Pool, current_process, cpu_count
from itertools import product
import argparse

from Simulation import Simulation


# We use a function with a global var here over a closure in __main__ because non-module-level functions are not
# callable by Pool.starmap for some reason
def start_sim(epp: float, eps: float, *vars_values: float) -> None:
	"""
	Start the simulation by creating a Simulation and running it
	:param float epp:          Self-interation of polymer
	:param float eps:          Interaction of polymer with solvent
	:param float *vars_values: Custom variable values
	"""
	# Reconstruct vars dict
	vars = {k: v for k, v in zip(args.variable.keys(), vars_values)}

	sim = Simulation(args.lammps_path, args.run, args.dry_run, current_process().name)
	sim.sample_coord(epp, eps, vars)


def init_pool(args_dict: dict) -> None:
	"""
	Initialise workers with arguments dict as global args
	:param args_dict: Arguments
	"""
	global args
	args = args_dict


if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("epp", type=lambda s: [float(i) for i in s.split(',')],
	                    help="Comma-separated list of Epp values")
	parser.add_argument("eps", type=lambda s: [float(i) for i in s.split(',')],
	                    help="Comma-separated list of Eps values")

	# Create dict of lists from argument string where several variables are separated by spaces, variable names and
	# their values are separated by =, and values are a comma-separated list
	parser.add_argument("-var", "--variable", default={}, type=lambda s:
	                    {k: [float(i) for i in v.split(',')] for k, v in [var.split('=') for var in s.split(' ')]},
	#                   ^ *Sometimes my genius is... it's almost frightening.*
	                    help="Custom equal-style variable(s) to set. Can be arrays, with values separated by commas. "
	                         "Multiple variables should be separated by spaces. Values should be floats. Example: -var "
	                         "mu=1.0, 2.0 cps=1.5,2.0",
	                    metavar="VAR=VALUE")

	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp_daily',
	                    help="Path to the LAMMPS binary. May be a command, like \"mpirun lmp\"")
	parser.add_argument("-r", "--run", type=int, default=9000000, help="Run GCMC for n timesteps")
	args = parser.parse_args()

	# Create cartesian product of two parameters. Returns list of tuples (epp, eps, *vars)
	coordList = list(product(args.epp, args.eps, *args.variable.values()))

	print("Got {} jobs, distributed over {} workers:".format(len(coordList), cpu_count()))
	print(*coordList, sep="\n")

	# Create pool of number of cores workers
	with Pool(cpu_count(), initializer=init_pool, initargs=(args,)) as p:
		p.starmap(start_sim, coordList)
