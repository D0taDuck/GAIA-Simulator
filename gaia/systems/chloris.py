"""Chloris: vegetation, flowers, seeds, and edible forage."""

import math


class Chloris:
    name = "Chloris"

    def step(self, sim):
        w, c = sim.world, sim.config
        season = 1 + 0.45 * math.sin(2 * math.pi * w.tick / c.season_length)
        water_factor = min(1.0, w.water / (c.water_capacity * 0.15))
        pollution_factor = 1 / (1 + w.pollution * c.plant_pollution_sensitivity)
        seed_factor = min(1.0, w.seed_bank / max(1.0, c.seed_bank_capacity * 0.20))
        space = max(0.0, 1 - w.plant_biomass / c.plant_biomass_capacity)

        potential = c.food_growth * season * w.fertility * water_factor * pollution_factor * seed_factor * space
        water_limited = w.water / c.plant_water_cost if c.plant_water_cost else float("inf")
        growth = max(0.0, min(potential, water_limited, c.plant_biomass_capacity - w.plant_biomass))
        w.water -= growth * c.plant_water_cost
        w.plant_biomass += growth
        w.seed_bank = max(0.0, w.seed_bank - growth * 0.10)

        dieback = min(w.plant_biomass, w.plant_biomass * c.plant_dieback * (1 + w.pollution * c.plant_pollution_sensitivity))
        w.plant_biomass -= dieback
        flowering_season = min(1.0, max(0.0, (season - 0.55) / 0.45))
        w.flowering_biomass = w.plant_biomass * c.flowering_fraction * flowering_season
        seed_input = w.flowering_biomass * c.seed_yield * (1 + w.pollination_bonus)
        w.seed_bank = min(c.seed_bank_capacity, max(0.0, w.seed_bank * (1 - c.seed_decay) + seed_input))

        forage = min(c.wild_food_capacity - w.wild_food, growth * c.forage_from_growth * (1 + w.pollination_bonus))
        w.wild_food += max(0.0, forage)
        w.plant_growth = growth
        w.plant_dieback = dieback
        w.forage_yield = w.natural_growth = max(0.0, forage)
        if w.tick % c.governance_interval == 0:
            sim.log(self.name, f"Vegetation {w.plant_biomass:.1f}; flowers {w.flowering_biomass:.1f}; forage {w.forage_yield:.1f}")
