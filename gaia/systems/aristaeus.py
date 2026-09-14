"""Pollinators and grazers: productive species with individual life cycles."""

import math

from ..genetics import Creature, inherit_resilience


class Aristaeus:
    name = "Aristaeus"

    @staticmethod
    def _advance(creatures, *, max_age, stress, recovery=0.01, adaptation_strength=0.0):
        survivors = []
        deaths = 0
        for creature in creatures:
            creature.age += 1
            creature.cooldown = max(0, creature.cooldown - 1)
            resilience = creature.resilience if adaptation_strength else 0.0
            effective_stress = stress * (1 - adaptation_strength * resilience)
            effective_recovery = recovery * (0.75 + 0.50 * resilience) if adaptation_strength else recovery
            creature.health = min(1.0, creature.health + effective_recovery - effective_stress)
            if creature.health <= 0 or creature.age >= max_age:
                deaths += 1
            else:
                survivors.append(creature)
        return survivors, deaths

    def step(self, sim):
        w, c = sim.world, sim.config
        habitat = w.fertility * min(1.0, w.flowering_biomass / max(1.0, c.plant_biomass_capacity * c.flowering_fraction * 0.40))
        pollution_stress = min(1.0, w.pollution * c.pollinator_pollution_sensitivity)

        sim.pollinators, pollinator_deaths = self._advance(
            sim.pollinators, max_age=c.pollinator_max_age,
            stress=(1 - habitat) * c.pollinator_starvation_damage + pollution_stress, recovery=0.05,
            adaptation_strength=c.pollinator_adaptation_strength,
        )
        eligible_pollinators = [creature for creature in sim.pollinators if creature.age >= c.pollinator_maturity_age and creature.health > 0.55 and not creature.cooldown]
        pollinator_births = []
        # Pollinators have no population ceiling.  As density rises their
        # reproduction falls continuously, leaving room for natural overshoot
        # and decline without abruptly stopping births at one exact count.
        crowding = math.exp(-len(sim.pollinators) / c.pollinator_pressure_scale)
        for parent in eligible_pollinators:
            if sim.life_rng.random() < c.pollinator_birth_probability * habitat * crowding:
                pollinator_births.append(Creature(sim.next_creature_id, "pollinator", generation=parent.generation + 1,
                                                  resilience=inherit_resilience(parent, parent, sim.life_rng, c.pollinator_adaptation_mutation)))
                sim.next_creature_id += 1
                parent.cooldown = 5
                parent.offspring += 1
        sim.pollinators.extend(pollinator_births)
        w.pollinator_count = len(sim.pollinators)
        # More insects can always exist, but a finite amount of flowering
        # habitat means each additional pollinator contributes less than the
        # one before it.
        w.pollination_bonus = c.pollination_bonus_max * (1 - math.exp(-w.pollinator_count / c.pollinator_effect_scale))

        w.livestock_food = 0.0
        grazing_need = len(sim.grazers) * c.grazer_wild_food_per_animal
        water_need = len(sim.grazers) * c.grazer_water_per_animal
        grazing = min(w.plant_biomass, grazing_need)
        water = min(w.water, water_need)
        resource_share = min(grazing / grazing_need if grazing_need else 1.0, water / water_need if water_need else 1.0)
        w.plant_biomass -= grazing
        w.water -= water
        w.livestock_food = min(c.food_capacity - w.food, len(sim.grazers) * c.grazer_food_yield * resource_share)
        w.food += w.livestock_food
        w.pollution += len(sim.grazers) * c.grazer_pollution_per_animal

        # Dense herds suffer compounding competition for shelter, forage, and
        # disease resistance. This is pressure, not a numerical population cap.
        density_pressure = (len(sim.grazers) / c.grazer_pressure_scale) ** 2
        sim.grazers, grazer_deaths = self._advance(
            sim.grazers, max_age=c.grazer_max_age,
            stress=(1 - resource_share) * c.grazer_starvation_damage + density_pressure * c.grazer_density_stress,
            recovery=0.025, adaptation_strength=c.grazer_adaptation_strength,
        )
        eligible_grazers = [creature for creature in sim.grazers if creature.age >= c.grazer_maturity_age and creature.health > 0.65 and not creature.cooldown]
        sim.life_rng.shuffle(eligible_grazers)
        grazer_births = []
        crowding = 1 / (1 + len(sim.grazers) / c.grazer_pressure_scale)
        if resource_share > 0.65:
            for first, second in zip(eligible_grazers[::2], eligible_grazers[1::2]):
                inherited_resilience = inherit_resilience(first, second, sim.life_rng, c.grazer_adaptation_mutation)
                adaptation = 0.75 + 0.50 * inherited_resilience
                if sim.life_rng.random() < c.grazer_birth_probability * habitat * crowding * adaptation:
                    grazer_births.append(Creature(sim.next_creature_id, "grazer", generation=max(first.generation, second.generation) + 1,
                                                  resilience=inherited_resilience))
                    sim.next_creature_id += 1
                    first.cooldown = second.cooldown = 12
                    first.offspring += 1
                    second.offspring += 1
        sim.grazers.extend(grazer_births)
        w.grazer_count = len(sim.grazers)
        w.grazer_births = len(grazer_births)
        w.grazer_deaths = grazer_deaths
        if w.tick % c.governance_interval == 0:
            sim.log(self.name, f"Pollinators {w.pollinator_count} (+{len(pollinator_births)}/-{pollinator_deaths}); grazers {w.grazer_count} (+{len(grazer_births)}/-{grazer_deaths})")
