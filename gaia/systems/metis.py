"""A transparent feedback controller driven by the world's own observations."""

from statistics import mean


class Metis:
    name = "Metis"

    def step(self, sim):
        w, c = sim.world, sim.config
        if not c.metis_enabled or c.mode == "off":
            w.ecosystem_pressure = w.feedback_response = 0.0
            w.biodiversity = 1.0
            return

        food_security = min(1.0, w.food / (c.food_capacity * 0.45))
        water_security = min(1.0, w.water / (c.water_capacity * 0.35))
        pollinator_retention = min(1.0, w.pollinator_count / max(1, c.initial_pollinators))
        grazer_retention = min(1.0, w.grazer_count / max(1, c.initial_grazers))
        w.biodiversity = (pollinator_retention + grazer_retention) / 2

        recent = sim.history[-c.feedback_window:]
        shortage = mean(row["shortage"] for row in recent) if recent else 0.0
        fertility_loss = 1 - w.fertility
        resource_pressure = 1 - min(food_security, water_security)
        biodiversity_pressure = 1 - w.biodiversity
        raw_pressure = min(1.0, 0.40 * resource_pressure + 0.25 * shortage + 0.20 * fertility_loss + 0.15 * biodiversity_pressure)
        # Smooth the signal so a single poor tick does not cause a control
        # oscillation, while persistent decline still changes behavior.
        w.ecosystem_pressure = 0.70 * w.ecosystem_pressure + 0.30 * raw_pressure
        w.feedback_response = min(1.0, w.ecosystem_pressure * c.feedback_gain)
        if w.tick % c.governance_interval == 0:
            sim.log(self.name, f"Pressure {w.ecosystem_pressure:.0%}; biodiversity {w.biodiversity:.0%}; response {w.feedback_response:.0%}")
