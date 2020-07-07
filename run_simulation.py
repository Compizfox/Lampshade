"""
Deserialise variables passed as CLI arguments and instantiate and run a Simulation
"""

from sys import argv
import json

from Simulation import Simulation

lammps_command = json.loads(argv[1])
input_filename = json.loads(argv[2])
log_filename = json.loads(argv[3])
dry_run = json.loads(argv[4])
static_vars = json.loads(argv[5])
dyn_vars = json.loads(argv[6])

sim = Simulation(lammps_command, input_filename, log_filename, dry_run, True)
sim.run_gcmc(static_vars, dyn_vars)
