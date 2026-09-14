import math


class NaturalProcesses:
    name = "Nature"

    def step(self, sim):
        w, c = sim.world, sim.config
        season = 1 + 0.45 * math.sin(2 * math.pi * w.tick / c.season_length)
        w.rainfall = max(0.0, c.rainfall * season * sim.weather_rng.uniform(1 - c.rainfall_variability, 1 + c.rainfall_variability))
        w.reservoir = min(c.reservoir_capacity, w.reservoir + w.rainfall)
        w.transfer_water(c.natural_flow, c.water_capacity)
        w.water *= 1 - c.evaporation
        w.food_spoilage = w.food * c.food_decay * (1 - w.preservation)
        w.food = max(0.0, w.food - w.food_spoilage)
        w.pollution *= 1 - c.pollution_decay
        w.thor_harvest = 0.0
        w.fertility = min(1.0, max(0.0, w.fertility + c.fertility_recovery * (1 - w.fertility) - w.pollution * 0.000001))
        water_factor = min(1.0, w.water / (c.water_capacity * 0.15))
        pollution_factor = 1 / (1 + w.pollution / 100)
