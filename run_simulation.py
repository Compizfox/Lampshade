"""
Deserialise variables passed as CLI arguments and instantiate and run a Simulation
"""

from sys import argv
import json

from Simulation import Simulation

lammps_command = json.loads(argv[1])
dry_run = json.loads(argv[2])
static_vars = json.loads(argv[3])
dyn_vars = json.loads(argv[4])

sim = Simulation(lammps_command, dry_run, True)
sim.run_gcmc(static_vars, dyn_vars)
