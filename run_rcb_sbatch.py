#!/usr/bin/env python3

"""
Refines grid using pairwise recursive bisectioning (RCB) sampling

The pairs come from the results of the grid sampling; they are pairs of points that cross a regime boundary.
Bisectioning will occur between the pairs until the distance is less than RCB_THRESHOLD.
Runs one bisectioning job with MPI. The bisectioning starts in bisection_job() with an
equilibration and long initial GCMC run of 9M timesteps. bisection_job() then calls recursive_bisect() to start the real
bisectioning; the first iteration will not be simulated because it was the initial run.

This version of the RCB script does not use the LAMMPS Python library, multiprocessing, or MPI. Rather, it is called in
a sbatch job script and spawns MPI-enabled LAMMPS simulations using srun.
Resuming of simulation is handled using restart files.
"""

from os import mkdir, chdir, path, environ
from typing import Tuple, List
from datetime import datetime
from subprocess import run, DEVNULL
from io import StringIO

import numpy as np

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


def sample_coord(last_restart_filename: str, epp: float, eps: float) -> Tuple[int, str]:
	"""
	Simulate a system with the given parameters and analyse the results to return a regime classification.
	:param last_restart_filename: Filename of the restart file to resume from.
	:param epp: self-interaction of polymer
	:param eps: interaction of polymer with solvent
	:return:    Classification
	"""
	# Build LAMMPS input script
	buf = StringIO()
	buf.write('variable epp equal {}\n'.format(epp))
	buf.write('variable eps equal {}\n'.format(eps))
	buf.write('read_restart {}\n'.format(last_restart_filename))
	# GCMC run (continuing from restart, 6M timesteps)
	with open('in.b_gcmc_rcb_fromrestart') as f:
		buf.write(f.read())
	buf.write('run 6000000\n')
	buf.write('write_data data.gcmc\n')
	buf.write('write_restart restart.gcmc\n')

	subdir = 'rcb_{}_{}'.format(epp, eps)
	run_in_subdir(buf.getvalue(), subdir)

	rc = RegimeClassifier(subdir)
	return rc.get_classification(), '../{}/restart.gcmc'.format(subdir)


def recursive_bisect(last_restart_filename: str, l: Tuple[float, float], r: Tuple[float, float]) -> None:
	"""
	Returns the middlepoint between two coords
	:param last_restart_filename: Filename of the restart file to resume from.
	:param l:   Left coord
	:param r:   Right coord
	"""
	if np.linalg.norm(np.array(l) - np.array(r)) > RCB_THRESHOLD:
		# Calculate midpoint between two bounds
		midpoint = tuple((np.array(l) + np.array(r)) / 2)

		# Run simulation
		print("{}: Simulating {}...".format(datetime.now(), midpoint))
		classification, last_restart_filename = sample_coord(last_restart_filename, *midpoint)

		# Determine if we're to the left or right
		try:
			if REGIMES.index(classification) == 0:
				# We're to the left, make current coord the left bound and recurse
				return recursive_bisect(last_restart_filename, midpoint, r)
			elif REGIMES.index(classification) == 1:
				# We're to the right, make current coord the right bound and recurse
				return recursive_bisect(last_restart_filename, l, midpoint)
		except ValueError:
			raise RuntimeError("This should not happen. Classification = {}".format(classification))

	print("{}: Finished RCB (distance below threshold).".format(datetime.now()))


def bisection_job(l: Tuple[float, float], r: Tuple[float, float]) -> None:
	"""
	Runs equilibration and initial GCMC run.
	Then calls recursive_bisect().
	:param l: Left coord
	:param r: Right coord
	"""
	# Calculate midpoint between two bounds for equilibration
	midpoint = tuple((np.array(l) + np.array(r)) / 2)
	epp, eps = midpoint

	# Build LAMMPS input script
	buf = StringIO()
	buf.write('variable epp equal {}\n'.format(epp))
	buf.write('variable eps equal {}\n'.format(eps))
	# 'header' of equilibration input file
	with open('in.b_equi_header') as f:
		buf.write(f.read())
	# Equilibration
	with open('in.b_equi_run') as f:
		buf.write(f.read())
	# Initial GCMC run (from scratch, 9M timesteps)
	with open('in.b_gcmc_rcb') as f:
		buf.write(f.read())
	buf.write('run 9000000\n')
	buf.write('write_data data.gcmc\n')
	buf.write('write_restart restart.gcmc\n')

	print("{}: Starting equilibration and initial GCMC run (epp={}, eps={})...".format(datetime.now(), epp, eps))
	subdir = 'rcb_{}_{}'.format(epp, eps)
	run_in_subdir(buf.getvalue(), subdir)

	# Start recursive bisectioning
	print("{}: Starting RCB...".format(datetime.now()))
	recursive_bisect('../{}/restart.gcmc'.format(subdir), l, r)


def run_in_subdir(input_script: str, subdir: str) -> None:
	"""
	Runs a simulation in a subdirectory.
	:param input_script: String containing the LAMMPS input script.
	:param subdir: String containing the subdirectory to run the simulation in.
	"""
	# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
	if not path.isdir(subdir):
		mkdir(subdir)
		chdir(subdir)
		run('lmp_daily', input=input_script, universal_newlines=True, stdout=DEVNULL)
		chdir('../')


if __name__ == '__main__':
	# Read from SLURM_ARRAY_TASK_ID environment variable which pair to run
	pair = pairs[environ['SLURM_ARRAY_TASK_ID']]
	bisection_job(*pair)
