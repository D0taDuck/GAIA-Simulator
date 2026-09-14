# GAIA Simulator

**A reproducible artificial ecosystem and civilization simulation for exploring how complex systems emerge, adapt, stabilize, and fail.**

GAIA is an experimental Python simulation built around a simple question:

> What happens if we stop telling a simulated world what equilibrium should look like, give it mechanisms capable of producing equilibrium, and observe what emerges?

Rather than forcing populations or resources toward predetermined outcomes, GAIA models interacting environmental, ecological, agricultural, demographic, and adaptive systems. A run can stabilize, oscillate, grow, collapse, recover, or end in extinction depending on the conditions produced by those interactions.

The project is designed as an experimental system rather than a calibrated prediction of the real world. Its purpose is to make feedback loops observable and reproducible so they can be tested over long simulation runs.

## What GAIA Models

GAIA's world is built from interconnected systems rather than a single population equation. Current systems include:

- finite water and reservoir dynamics
- rainfall, evaporation, seasonal effects, and environmental pressure
- plant biomass, seed banks, flowering, pollination, and wild forage
- agriculture, farm labor, soil fertility, and resource depletion
- pollinator and grazer populations
- human inhabitants with health, aging, reproduction, and inherited traits
- food production, storage, preservation, consumption, and shortages
- pollution generation, decay, and ecological consequences
- governance and adaptive feedback
- scheduled environmental events such as drought, rainfall, blight, disease, and food shocks
- seeded runs, checkpoints, metrics, chronicles, and CSV export for reproducible experiments

A central design rule is that resources should come from mechanisms inside the world. Feedback systems can change behavior, but they should not simply create resources or override mortality to force a desired outcome.

## System Architecture

GAIA uses named subsystems to separate responsibilities and make the simulation easier to inspect.

| System | Responsibility |
| --- | --- |
| **Gaia / Engine** | Coordinates simulation state and tick execution |
| **Environment** | Climate and environmental processes |
| **Poseidon** | Water management and reservoir release |
| **Chloris** | Plant biomass, seeds, flowering, and vegetation growth |
| **Demeter** | Agriculture, farming, foraging, and labor allocation |
| **Aristaeus** | Pollinators, grazers, and productive animal ecology |
| **Hestia** | Settlement stewardship, food preservation, and demographic pressure |
| **Metis** | Transparent ecological feedback and adaptive pressure |
| **Population** | Human health, consumption, aging, reproduction, and mortality |
| **Governance** | Optional governance behavior |
| **Thor** | Optional food intervention / legacy resource support |

These systems interact through shared world state. For example, the agricultural cycle connects rainfall and reservoir water to vegetation, pollinators, soil fertility, farm labor, food availability, and ultimately population health and reproduction.

See [AGRICULTURE.md](AGRICULTURE.md) for a deeper explanation of the current ecological and agricultural cycle.

## Emergent Behavior

GAIA deliberately avoids protecting populations with guaranteed minimums or simply assigning a fixed equilibrium. Humans, pollinators, and grazers can grow, fluctuate, adapt, or disappear.

This makes failure useful data rather than necessarily a software failure. A population collapse may expose a resource bottleneck, delayed feedback, demographic overshoot, ecological imbalance, or a missing mechanism. The simulation can also continue after human extinction, allowing the remaining ecosystem to be observed independently.

Inherited variation is included in human genomes and animal resilience traits. Organisms better suited to the conditions they encounter can have different survival and reproductive outcomes, allowing population characteristics to change over generations without specifying a desired evolutionary direction.

## Reproducible Experiments

GAIA is intended to support repeated experimental runs. Configuration files and random seeds allow scenarios to be compared under controlled starting conditions.

Examples of useful experiments include:

- comparing feedback modes under the same seed
- disabling agriculture to test whether foraging alone can sustain inhabitants
- changing farm land or yield to study agricultural limits
- increasing agricultural pollution costs to study productive but degrading regimes
- altering ecological food regeneration
- testing population behavior without artificial species caps
- introducing drought, disease, blight, or food shocks at controlled ticks
- observing whether ecological populations stabilize, oscillate, run away, adapt, or collapse

The goal is not to prove that a particular outcome *should* occur. The goal is to understand why an outcome occurred under a defined set of mechanisms and initial conditions.

## Running GAIA

GAIA requires **Python 3.11 or newer**.

From the repository directory:

```bash
python launch.py
```

or:

```bash
python -m gaia
```

On Windows, the repository also includes:

```text
Launch Gaia.cmd
run.ps1
```

The default launcher starts the local GAIA server/monitor interface.

## Repository Structure

```text
GAIA-Simulator/
├── gaia/              # Current simulation package
│   ├── systems/       # Environmental, ecological, and population systems
│   ├── engine.py      # Simulation coordination
│   ├── world.py       # World state
│   ├── genetics.py    # Inherited traits and variation
│   ├── events.py      # Scheduled simulation events
│   ├── metrics.py     # Observation and metrics
│   ├── storage.py     # Persistence and run data
│   ├── server.py      # Local monitor server
│   └── monitor.html   # Browser-based monitoring interface
├── configs/           # Ready-to-edit experimental configurations
├── tests/             # Simulation and subsystem tests
├── legacy/            # Preserved earlier implementation material
├── AGRICULTURE.md     # Agriculture/ecology documentation
├── launch.py          # Cross-environment launcher
└── pyproject.toml     # Project metadata
```

## Project Status

GAIA is an **experimental model under active development and stabilization**.

The current focus is not adding features for their own sake. The priority is validating interactions between systems, removing artificial constraints where possible, improving observability, and testing whether long seeded runs remain numerically and logically stable.

A software failure and an ecological failure are intentionally treated as different things: extinction can be a valid simulation outcome; corrupted state, impossible values, broken reproducibility, or crashes are not.

## Development

GAIA is an independently directed project developed with AI-assisted programming tools. AI has been used to assist with implementation, debugging, testing, scaling, and code analysis. The project's concepts, architecture, experimental direction, review, and decisions are human-directed.

## Disclaimer

GAIA is an experimental computational model. It is not intended to provide real-world ecological, demographic, agricultural, economic, or policy predictions. Results describe the behavior of the implemented model under its configured assumptions.

---

**Created by James Mason (`D0taDuck`)**
