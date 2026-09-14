# file: gaia_simulation.py
from panda3d.core import Point3
from direct.showbase.ShowBase import ShowBase
import simpy
import random
import pandas as pd
import string

#Global kill flag
kill_simulation = False

# Define the Environment class
class Environment:
    def __init__(self, env):
        self.env = env
        # Add attributes for resources, climate, etc.
        self.resources = {'water': 1000, 'food': 500}
        self.pollution = 0 #initalize pollution as an integer
        self.water_regulator= Posidon(env, self)
        self.food_regulator = Thor(env, self)

    def natural_processes(self):
        while True:
            # Define natural processes such as resource regeneration
            yield self.env.timeout(1)
            self.pollution -= 1
            self.pollution = max(0, self.pollution)
            print(f'Time {self.env.now}: Pollution: {self.pollution}')

class Posidon:
    def __init__(self, env, environment):
        self.env = env
        self.environment = environment
        self.action = env.process(self.regulate())

    def regulate(self):
        while True:
            yield self.env.timeout(10)  # Regulate every 10 time units
            self.environment.resources['water'] += 100  # Add water resource
            print(f"Time {self.env.now}: Water regulated, New water level: {self.environment.resources['water']}")


# Define the Thor class
class Thor:
    def __init__(self, env, environment):
        self.env = env
        self.environment = environment
        self.action = env.process(self.regulate())

    def regulate(self):
        while True:
            yield self.env.timeout(15)  # Regulate every 15 time units
            self.environment.resources['food'] += 50  # Add food resource
            print(f"Time {self.env.now}: Food regulated, New food level: {self.environment.resources['food']}")

# Define the Human class
class Human:
    def __init__(self, env, name, environment):
        self.env = env
        self.name = name
        self.environment = environment
        self.action = env.process(self.live())

    def live(self):
        while True:
            # Define human activities such as consuming resources
            yield self.env.timeout(random.randint(1, 5))
            self.environment.resources['water'] -= 1
            self.environment.resources['food'] -= 2
            print(f'Time {self.env.now}: {self.name} consumed resources')

class Organism:
    def __init__(self, name, genome):
        self.name = name
        self.genome = genome
        self.fitness = self.evaluate_fitness()

    def evaluate_fitness(self):
        # Simplified fitness function
        return sum(self.genome)
    
    def create_model(self, base):
        self.model = base.loader.loadModel("models/smiley")
        self.model.reparentTo(base.render)
        self.model.setPos(Point3(random.random() * 10, random.random() * 10, 0))

    def update(self):
        if self.model:
            self.model.setPos(self.model.getPos() + Point3(random.random() - 0.5, random.random() - 0.5, 0))

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.organisms = [self.create_organism() for _ in range(10)]
        self.taskMgr.add(self.update_task, "update_task")

    def create_organism(self):
        name = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
        genome = [random.randint(0, 10) for _ in range(10)]
        organism = Organism(name, genome)
        organism.create_model(self)
        return organism

    def update_task(self, task):
        for organism in self.organisms:
            organism.update()
        return task.cont

app = MyApp()
app.run()
def generate_name():
    # Generate a random name with 5 letters
    return ''.join(random.choices(string.ascii_uppercase, k=5))

def crossover(parent1, parent2):
    # Single-point crossover
    point = random.randint(1, len(parent1.genome) - 1)
    child1 = Organism(generate_name(), parent1.genome[:point] + parent2.genome[point:])
    child2 = Organism(generate_name(), parent2.genome[:point] + parent1.genome[point:])
    return child1, child2

def mutate(organism, mutation_rate=0.01):
    # Mutation function
    new_genome = [
        gene if random.random() > mutation_rate else random.randint(0, 10)
        for gene in organism.genome
    ]
    return Organism(generate_name(), new_genome)

def evolve(population, generations=100):
    for generation in range(generations):
        # Selection: sort population by fitness and select the top 50%
        population = sorted(population, key=lambda x: x.fitness, reverse=True)
        next_generation = population[:len(population)//2]

        # Crossover and Mutation
        while len(next_generation) < len(population):
            parent1, parent2 = random.sample(population[:len(population)//2], 2)
            child1, child2 = crossover(parent1, parent2)
            next_generation.append(mutate(child1))
            next_generation.append(mutate(child2))

        population = next_generation

    return population

# Initial population with random names and genomes
initial_population = [Organism(generate_name(), [random.randint(0, 10) for _ in range(10)]) for _ in range(100)]

# Evolve the population
final_population = evolve(initial_population)
best_organism = max(final_population, key=lambda x: x.fitness)
print("Best organism name:", best_organism.name)
print("Best organism genome:", best_organism.genome)
print("Best organism fitness:", best_organism.fitness)


# Define the Governance class
class Governance:
    def __init__(self, env, environment):
        self.env = env
        self.environment = environment
        self.policies = []
        self.action = env.process(self.govern())

    def govern(self):
        while True:
            if kill_simulation:
                print(f"Simulation killed at time {self.env.now}")
                break
            yield self.env.timeout(10) # Implement policies every 10 days
            self.implement_policy()

    def implement_policy(self):
        policy = f"Policy at time {self.env.now}"
        self.policies.append(policy)
        # Example of policiy effect: Adjust resource levels
        self.environment.resources['water'] += 20
        self.environment.resources["food"] += 10
        self.environment.pollution -= 5
        print(f'Time {self.env.now}: {policy} implemented, Pollution: {self.environment.pollution}')

#Function to set the kill flag
def stop_simulation():
    global kill_simulation
    kill_simulation = True

# Simulation setup
def run_simulation(simulation_time=None):
    env = simpy.Environment()
    environment = Environment(env)
    humans = [Human(env, f'Human {i}', environment) for i in range(5)]
    governance = Governance(env, environment)
    
    env.process(environment.natural_processes())
    
    if simulation_time is not None:
        env.run(until=simulation_time)
    else:
        env.run()

if __name__ == '__main__':
    import threading

    # Run the simulation in a seperate thread
    simulation_thread = threading.Thread(target=run_simulation, kwargs={'simulation_time': None})
    simulation_thread.start()

    # Wait for some time then stop the simulation
    import time
    time.sleep(10)
    stop_simulation()

    #Wait for the simulation to finish
    simulation_thread.join()
    print("Simulation finished")
