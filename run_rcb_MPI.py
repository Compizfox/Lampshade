#!/usr/bin/env python3

"""
Refines grid using pairwise recursive bisectioning (RCB) sampling

The pairs come from the results of the grid sampling; they are pairs of points that cross a regime boundary.
Bisectioning will occur between the pairs until the distance is less than RCB_THRESHOLD.
Runs one bisectioning job with MPI. The bisectioning starts in bisection_job() with an
equilibration and long initial GCMC run of 9M timesteps. bisection_job() then calls recursive_bisect() to start the real
bisectioning; the first iteration will not be simulated because it was the initial run.

Meant for SLURM batch usage.
"""

from os import mkdir, chdir, path, environ
from typing import Tuple, List, Callable
from datetime import datetime

from lammps import lammps
import numpy as np
from mpi4py import MPI

from RegimeClassifier import RegimeClassifier

RCB_THRESHOLD = 0.05

# Boundary between regimes to probe
REGIMES = (2, 1)

# List of 2-tuples of 2-tuples, representing initial outer bound coords
pairs: List[Tuple[Tuple[float, float], Tuple[float, float]]] = [
	((1.0, 1.4), (1.4, 1.4)),
	((1.0, 1.4), (1.4, 1.0)),
	((1.0, 1.4), (1.0, 1.0)),
	((0.6, 1.0), (1.0, 1.0)),
	((0.6, 1.0), (0.6, 0.6)),
	((0.6, 1.4), (1.0, 1.0)),
]


def sample_coord(lmp: lammps, epp: float, eps: float) -> int:
	"""
	Simulate a system with the given parameters and analyse the results to return a regime classification.
	:param lmp: LAMMPS instance
	:param epp: self-interaction of polymer
	:param eps: interaction of polymer with solvent
	:return:    Classification
	"""
	def sim():
		lmp.command('variable epp equal {}'.format(epp))
		lmp.command('variable eps equal {}'.format(eps))
		# GCMC run (continuing, 6M timesteps)
		lmp.file('../in.b_gcmc_rcb')
		lmp.command('run 6000000')
		lmp.command('write_data	data.gcmc')

	subdir = 'rcb_{}_{}'.format(epp, eps)
	run_in_subdir(sim, subdir)

	rc = RegimeClassifier(subdir)
	return rc.get_classification()


def recursive_bisect(lmp, l: Tuple[float, float], r: Tuple[float, float]) -> None:
	"""
	Returns the middlepoint between two coords
	:param lmp: LAMMPS instance
	:param l:   Left coord
	:param r:   Right coord
	"""
	if np.linalg.norm(np.array(l) - np.array(r)) > RCB_THRESHOLD:
		# Calculate midpoint between two bounds
		midpoint = tuple((np.array(l) + np.array(r)) / 2)

		# Run simulation
		print("{}: Simulating {}...".format(datetime.now(), midpoint))
		classification = sample_coord(lmp, *midpoint)

		# Determine if we're to the left or right
		if REGIMES.index(classification) == 0:
			# We're to the left, make current coord the left bound and recurse
			return recursive_bisect(lmp, midpoint, r)
		elif REGIMES.index(classification) == 1:
			# We're to the right, make current coord the right bound and recurse
			return recursive_bisect(lmp, l, midpoint)
		else:
			raise RuntimeError("This should not happen. Classification = {}".format(classification))

	print("{}: Finished RCB (distance below threshold).".format(datetime.now()))


def bisection_job(l: Tuple[float, float], r: Tuple[float, float]) -> None:
	"""
	Instantiates a LAMMPS object and runs equilibration and initial GCMC run.
	Then calls recursive_bisect().
	:param l: Left coord
	:param r: Right coord
	"""
	# Calculate midpoint between two bounds for equilibration
	midpoint = tuple((np.array(l) + np.array(r)) / 2)

	# Instantiate LAMMPS object
	lmp = lammps(cmdargs=['-echo', 'log', '-screen', 'none'])

	epp, eps = midpoint

	def sim():
		lmp.command('variable epp equal {}'.format(epp))
		lmp.command('variable eps equal {}'.format(eps))
		# Run 'header' of equilibration input file
		lmp.file('../in.b_equi_header')
		# Equilibrate
		print("{}: Starting equilibration (epp={}, eps={})...".format(datetime.now(), epp, eps))
		lmp.file('../in.b_equi_run')
		# Initial GCMC run (from scratch, 9M timesteps)
		print("{}: Equilibration done. Starting initial GCMC run (epp={}, eps={})...".format(datetime.now(), epp, eps))
		lmp.file('../in.b_gcmc_rcb')
		lmp.command('run 9000000')
		lmp.command('write_data	data.gcmc')

	run_in_subdir(sim, 'rcb_{}_{}'.format(epp, eps))

	# Start recursive bisectioning
	print("{}: Starting RCB...".format(datetime.now()))
	recursive_bisect(lmp, l, r)

	lmp.close()


def run_in_subdir(func: Callable[[], None], subdir: str) -> None:
	"""
	Runs a simulation in a subdir.
	"""
	# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
	if not path.isdir(subdir):
		mkdir(subdir)
		chdir(subdir)
		func()
		chdir('../')


if __name__ == '__main__':
	# Read from SLURM_ARRAY_TASK_ID environment variable which pair to run
	pair = pairs[environ['SLURM_ARRAY_TASK_ID']]
	bisection_job(*pair)
