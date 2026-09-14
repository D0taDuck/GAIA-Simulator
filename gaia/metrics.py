"""Descriptive diagnostics, never a proof of equilibrium or endless collapse."""

from statistics import mean, pstdev


def diagnose(history, config):
    current = history[-1]
    if current["population"] == 0:
        return {"status": "extinct", "detail": "No inhabitants remain. Nature continues; automatic reseeding is disabled."}
    if current["population_limit_reached"]:
        return {"status": "capacity limit", "detail": "The computational population limit was reached; this run cannot establish balance."}
    window = config.observation_window
    if len(history) < window:
        return {"status": "observing", "detail": f"Collecting a {window}-tick observation window."}
    rows = history[-window:]
    shortage = mean(row["shortage"] for row in rows)
    if shortage > 0.12 or current["mean_health"] < 0.45:
        return {"status": "under stress", "detail": "Sustained unmet needs or poor population health in the recent window."}
    cvs, trends = [], []
    for key in ("population", "water", "food", "wild_food", "reservoir", "pollution", "fertility"):
        values = [r[key] for r in rows]
        scale = max(abs(mean(values)), 1.0 if key != "fertility" else 0.1)
        cvs.append(pstdev(values) / scale)
        quarter = max(1, window // 4)
        trends.append(abs(mean(values[-quarter:]) - mean(values[:quarter])) / scale)
    if max(cvs) < config.stability_tolerance and max(trends) < config.stability_tolerance and shortage < 0.01:
        return {"status": "locally steady", "detail": f"Low variation and drift across the last {window} ticks; long-term stability is unproven."}
    return {"status": "fluctuating", "detail": "The world remains populated, with measurable variation or drift. Cycles are not yet classified."}


def summarize(sim):
    rows = sim.history
    return {
        "seed": sim.config.seed, "mode": sim.config.mode, "ticks": sim.world.tick,
        "diagnosis": diagnose(rows, sim.config), "final_population": len(sim.population),
        "peak_population": max(r["population"] for r in rows),
        "extinction_tick": next((r["tick"] for r in rows if r["population"] == 0), None),
        "total_births": sum(r["births"] for r in rows), "total_deaths": sum(r["deaths"] for r in rows),
        "shortage_ticks": sum(r["shortage"] > 0.05 for r in rows),
        "final_pollinators": rows[-1].get("pollinator_count", 0),
        "final_grazers": rows[-1].get("grazer_count", 0),
        "capacity_limit_reached": sim.world.population_limit_reached,
    }
