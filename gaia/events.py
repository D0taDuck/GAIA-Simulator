"""Scheduled, visible environmental events for controlled Gaia experiments."""

import math


EVENT_TYPES = {"rainfall", "drought", "food_supply", "blight", "disease"}


def validate_event(data, current_tick):
    if not isinstance(data, dict) or set(data) != {"kind", "magnitude", "at_tick"}:
        raise ValueError("An event needs kind, magnitude, and at_tick")
    kind, magnitude, at_tick = data["kind"], data["magnitude"], data["at_tick"]
    if kind not in EVENT_TYPES:
        raise ValueError(f"Unknown event kind: {kind}")
    if isinstance(magnitude, bool) or not isinstance(magnitude, (int, float)) or not math.isfinite(magnitude) or magnitude <= 0:
        raise ValueError("Event magnitude must be a positive finite number")
    if kind == "disease" and magnitude > 1:
        raise ValueError("Disease severity must be between 0 and 1")
    if type(at_tick) is not int or at_tick <= current_tick:
        raise ValueError("Event tick must be in the future")
    return {"kind": kind, "magnitude": float(magnitude), "at_tick": at_tick}


def apply_event(sim, event):
    """Apply one due event. Every result is bounded by the world's stores."""
    w, c = sim.world, sim.config
    kind, amount = event["kind"], event["magnitude"]
    if kind == "rainfall":
        changed = min(amount, c.reservoir_capacity - w.reservoir)
        w.reservoir += changed
        detail = f"Rainfall added {changed:.1f} to the reservoir"
    elif kind == "drought":
        from_reservoir = min(amount, w.reservoir)
        w.reservoir -= from_reservoir
        from_water = min(amount - from_reservoir, w.water)
        w.water -= from_water
        detail = f"Drought removed {from_reservoir + from_water:.1f} stored water"
    elif kind == "food_supply":
        changed = min(amount, c.food_capacity - w.food)
        w.food += changed
        detail = f"Food supply added {changed:.1f} to the pantry"
    elif kind == "blight":
        changed = min(amount, w.wild_food)
        w.wild_food -= changed
        fertility_loss = min(0.25, changed / c.wild_food_capacity * 0.20)
        w.fertility = max(0.0, w.fertility - fertility_loss)
        w.pollution += changed * 0.01
        detail = f"Blight removed {changed:.1f} wild food and reduced soil fertility"
    else:  # disease
        for person in sim.population:
            person.health = max(0.0, person.health - amount)
        detail = f"Disease reduced inhabitant health by {amount:.0%}"
    sim.log("Event", detail)
