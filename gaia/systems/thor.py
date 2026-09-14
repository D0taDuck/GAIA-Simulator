class Thor:
    """Food production, preserving the role assigned in the original project."""

    name = "Thor"

    def step(self, sim):
        w, c = sim.world, sim.config
        if not c.thor_enabled or c.mode == "off" or w.tick % c.thor_interval:
            return
        amount = c.thor_harvest
        if c.mode == "feedback":
            amount = min(c.thor_harvest * 2, max(0.0, c.food_capacity * 0.5 - w.food))
        amount *= w.fertility / (1 + w.pollution / 150)
        grown = w.grow_food(amount, c)
        w.thor_harvest = grown
        if grown > 0:
            w.pollution += grown * 0.035
            sim.log(self.name, f"Produced {grown:.1f} food using water and soil fertility")
