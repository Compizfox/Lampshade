#!/usr/bin/env python3

"""
Samples a mesh grid in the 2D EPP-EPS parameter space.
No MPI; different points are simulated in parallel using Python multiprocessing.
"""

from multiprocessing import Pool, current_process
from itertools import product
from os import mkdir, chdir, path
from subprocess import run, DEVNULL
from io import StringIO
from datetime import datetime
import argparse


def sample_coord(epp: float, eps: float) -> None:
	"""
	Simulate a system with the given parameters
	:param epp: self-interation of polymer
	:param eps: interaction of polymer with solvent
	:return:
	"""
	# Build LAMMPS input script
	buf = StringIO()
	buf.write('variable epp equal {0:.2f}\n'.format(epp))
	buf.write('variable eps equal {0:.2f}\n'.format(eps))
	# 'header' of equilibration input file
	with open('in.b_equi_header') as f:
		buf.write(f.read())
	# Equilibration
	with open('in.b_equi_run') as f:
		buf.write(f.read())
	# Initial GCMC run (from scratch, 9M timesteps)
	with open('in.b_gcmc_rcb') as f:
		buf.write(f.read())
	buf.write('run {}\n'.format(args.run))
	buf.write('write_data data.gcmc\n')

	subdir = 'grid_{0:.2f}_{0:.2f}'.format(epp, eps)
	run_in_subdir(buf.getvalue(), subdir)


def run_in_subdir(input_script: str, subdir: str) -> None:
	"""
	Runs a simulation in a subdirectory.
	:param input_script: String containing the LAMMPS input script.
	:param subdir: String containing the subdirectory to run the simulation in.
	"""
	# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
	if not path.isdir(subdir):
		print("{} {}: Simulating {}...".format(datetime.now(), current_process().name, subdir))
		if not args.dry_run:
			mkdir(subdir)
			chdir(subdir)
			run(args.lammps_path, input=input_script, universal_newlines=True, stdout=DEVNULL, shell=True)
			chdir('../')
			print("{} {}: Finished {}.".format(datetime.now(), current_process().name, subdir))
	else:
		print("{} {}: Found existing subdir {}. Skipping.".format(datetime.now(), current_process().name, subdir))


if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("epp", type=lambda s: [float(i) for i in s.split(',')], help="Comma-separated list of EPP values")
	parser.add_argument("eps", type=lambda s: [float(i) for i in s.split(',')], help="Comma-separated list of EPS values")
	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp_daily', help="Path to the LAMMPS binary")
	parser.add_argument("-r", "--run", type=int, default=9000000, help="Run GCMC for n timesteps")
	args = parser.parse_args()

	# Create cartesian product of two parameters. Returns list of tuples (epp, eps)
	coordList = list(product(args.epp, args.eps))

	# Create pool of number of cores workers
	with Pool() as p:
		outputList = p.starmap(sample_coord, coordList)
