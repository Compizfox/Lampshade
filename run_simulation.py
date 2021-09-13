"""
Deserialise variables passed as CLI arguments and instantiate and run a Simulation
"""

from sys import argv
import json

from Simulation import Simulation

lammps_command = json.loads(argv[1])
input_filename = json.loads(argv[2])
log_filename = json.loads(argv[3])
initial_data_file_prefix = json.loads(argv[4])
dry_run = json.loads(argv[5])
static_vars = json.loads(argv[6])
dyn_vars = json.loads(argv[7])

sim = Simulation(lammps_command, input_filename, log_filename, initial_data_file_prefix, dry_run, True)
sim.run(static_vars, dyn_vars)
