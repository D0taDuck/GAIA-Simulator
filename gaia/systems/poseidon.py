class Poseidon:
    """Move water from a finite reservoir. Original name was spelled Posidon."""

    name = "Poseidon"

    def step(self, sim):
        w, c = sim.world, sim.config
        if not c.poseidon_enabled or c.mode == "off" or w.tick % c.poseidon_interval:
            return
        amount = c.poseidon_transfer
        if c.mode == "feedback":
            deficit = max(0.0, c.water_capacity * 0.55 - w.water)
            amount = min(c.poseidon_transfer * 2, deficit)
        moved = w.transfer_water(amount, c.water_capacity)
        if moved > 0:
            w.pollution += moved * 0.008
            sim.log(self.name, f"Transferred {moved:.1f} water from the reservoir")


Posidon = Poseidon
