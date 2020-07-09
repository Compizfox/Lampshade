# SPiVHB
SPiVHB contains the input scripts and a Python wrapper around LAMMPS for more convenient execution of MD simulations
of polymer brushes in equilibrium of solvent vapours.
 
The Python wrapper makes it possible to define (a list of) simulation parameters in a `settings.ini` file and run
simulations for all (combinations of) parameters in a standard way, in a serial or parallel manner, as defined in
`settings.ini`.

The name comes from the working title of the project: "Solvent Partitioning in Vapour-Hydrated Brushes".

## Installation
Simply clone the repository using Git:

```console
foo@bar:~$ git clone https://github.com/Compizfox/SPiVHB.git
```

or download a release and extract it. The Git approach has the advantage that updating is as easy as `git pull`.

SPiVHB requires at least Python 3.6. No further setup is needed (apart from the usual LAMMPS setup, obviously); SPiVHB
does not depend on any Python libraries outside the Standard Library.

## Usage
### Creating a subdirectory for a job
The wrapper assumes that you create a subdirectory for every "job" (set of simulations corresponding to e.g. a parameter
sweep):

```console
foo@bar:~/SPiVHB$ mkdir example
```

In this directory, the wrapper expects two files: the initial data file (equilibrated polymer brush) and `settings.ini`.
The name of the initial data file is specified in `settings.ini`. Let's copy the included `settings.ini.example` to the
subdirectory we just created:

```console
foo@bar:~/SPiVHB$ cd example
foo@bar:~/SPiVHB/example$ cp ../settings.ini.example settings.ini
```

### `settings.ini`
Now, it's up to you to set the correct values in `settings.ini` depending on what you want to do. Here is a quick
rundown of the various variables:

- `LAMMPS_path`: Path to the LAMMPS executable, which is simply `lmp` on most systems. Change this if LAMMPS is
  installed under a different name on your system.
- `LAMMPS_arguments`: Arguments to always pass to LAMMPS. Defaults to `-sf omp` to use the `OMP` versions of styles for
  free speed-up.
- `MPI_path`: Path to the mpirun/srun executable.
- `MPI_arguments` Arguments to pass to the mpirun/srun executable. Empty by default.

- `required_gcmc_vars`: List of variables that need to be passed to LAMMPS. Reflects the variables used in the input
  file `gcmc.in`.
- `slurm_sbatch_args`: sbatch command for submitting jobs (`SlurmJob` specific). Append to this the appropriate sbatch
  options (such as `-t xx:xx` and `-n x` for the time limit and number of processors respectively).
- `input_file`: Name of the LAMMPS input file
- `log_file`: Name of the log file to write (inside the inner simulation directory)

`[gcmc_vars]` contains LAMMPS variables and their values that are static within a job, i.e. the variables that do not
change in a parameter sweep.

`[gcmc_dyn_vars]` on the other hand contains the 'dynamic' variables: those that are varied within a parameter sweep.
Values are specified space-separated, and a simulation is spawned for every combination of values.

### Running
To run a job, execute `run_slurm.py` from the SPiVHB directory with the name of the job's subdirectory as argument:

```console
foo@bar:~/SPiVHB$ ./run_slurm.py example
```

The wrapper automatically creates subdirectories inside the job directory for every simulation. The output of the
simulation is placed in these subdirectories.

## Developer documentation
`Job` defines a abstract class for a job (a range of simulations with some specified parameters), including the argument
and setting parser. Simulations are spawned by calling the abstract method `_spawn_simulations()`.

In the current version, the only simulation spawn engine is `SlurmJob` (`run_slurm.py`) which targets SLURM, but it is
possible to e.g. run simulations interactively in serial or in parallel using multiprocessing by extending `Job` and
implementing `_spawn_simulations()` as appropriate.

`SlurmJob` writes an 'ephemeral' SLURM jobscript and pipes it to sbatch (as defined by `slurm_sbatch_args` in
`settings.ini`). The jobscript (which runs on the compute node at runtime) contains a call to `run_simulation.py` with
various required variables dumped JSON-encoded as arguments.

`run_simulation.py` then JSON-decodes these variables from `argv`, instantiates a `Simulation` and calls `run_gcmc()` on
it to start the simulation.

A `Simulation` creates a subdirectory and runs LAMMPS in a subprocess with the applicable variables.

Shown below is a diagram illustration the execution flow:

![Flow diagram](diagram.svg)