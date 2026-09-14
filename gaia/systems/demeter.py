"""Agriculture: human labor turns land, water, and fertility into food."""


class Demeter:
    name = "Demeter"

    def step(self, sim):
        w, c = sim.world, sim.config
        w.wild_harvest = w.farm_harvest = 0.0
        w.farm_workers = w.foragers = 0
        if not sim.population:
            return

        population = len(sim.population)
        available_workers = max(0, population - w.preservation_workers)
        # A hungry settlement reallocates labor toward cultivation, but always
        # leaves some people available to forage and sustain other work.
        pantry_ratio = min(1.0, w.food / (c.food_capacity * 0.45))
        shortage_pressure = max(0.0, 1 - pantry_ratio)
        labor_fraction = c.farm_labor_fraction
        if c.mode == "feedback":
            labor_fraction = min(0.80, labor_fraction + shortage_pressure * 0.42)
        if not c.demeter_enabled:
            labor_fraction = 0.0
        w.farm_workers = min(available_workers, round(available_workers * labor_fraction))
        w.foragers = available_workers - w.farm_workers

        ranked_farmers = sorted(sim.population, key=lambda person: person.agriculture_skill, reverse=True)
        farmers = ranked_farmers[:w.farm_workers]
        farmer_ids = {person.identifier for person in farmers}
        foragers = sorted((person for person in sim.population if person.identifier not in farmer_ids), key=lambda person: person.foraging_skill, reverse=True)[:w.foragers]
        w.mean_farmer_skill = sum(person.agriculture_skill for person in farmers) / len(farmers) if farmers else 0.0
        w.mean_forager_skill = sum(person.foraging_skill for person in foragers) / len(foragers) if foragers else 0.0

        # Foragers do not create food: they only move an existing wild stock
        # into the settlement's pantry.
        w.harvest_wild_food(sum(person.foraging_skill for person in foragers) * c.forage_per_inhabitant, c)

        if not w.farm_workers:
            return
        farm_work = sum(person.agriculture_skill for person in farmers)
        labor_factor = farm_work / (farm_work + c.farm_labor_half_saturation)
        water_factor = min(1.0, w.water / (c.water_capacity * 0.15))
        pollution_factor = 1 / (1 + w.pollution / 120)
        potential = c.farm_yield * c.farm_land * labor_factor * w.fertility * water_factor * pollution_factor * (1 + w.pollination_bonus)
        harvested = w.grow_farm_food(potential, c)
        if harvested:
            w.pollution += harvested * c.farm_pollution_per_food
            sim.log(self.name, f"{w.farm_workers} farmers harvested {harvested:.1f}; {w.foragers} foraged {w.wild_harvest:.1f}")
