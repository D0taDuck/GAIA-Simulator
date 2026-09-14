import argparse
import csv
from dataclasses import replace
import json
from pathlib import Path

from .config import Config
from .engine import Simulation
from .metrics import summarize
from .storage import export_run, load


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gaia autonomous world experiment")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "serve", "batch"):
        p = commands.add_parser(name)
        p.add_argument("--config", type=Path)
        if name != "batch":
            p.add_argument("--seed", type=int)
            p.add_argument("--mode", choices=("fixed", "feedback", "off"))
            p.add_argument("--resume", type=Path)
        if name in ("run", "batch"):
            p.add_argument("--ticks", type=int, default=2000)
            p.add_argument("--output", type=Path, default=Path("runs") / name)
        if name == "batch":
            p.add_argument("--seeds", type=int, nargs="+", default=list(range(1, 11)))
            p.add_argument("--modes", nargs="+", choices=("fixed", "feedback", "off"), default=["off", "fixed", "feedback"])
            p.add_argument("--full-runs", action="store_true", help="Also save every checkpoint, history and HTML report")
        if name == "serve":
            p.add_argument("--port", type=int, default=8765)
            p.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    try:
        if getattr(args, "ticks", 0) < 0:
            raise ValueError("ticks cannot be negative")
        if getattr(args, "resume", None) and (args.config or args.seed is not None or args.mode):
            raise ValueError("A resumed run uses its saved configuration; omit --config, --seed and --mode")
        config = Config.from_dict(json.loads(args.config.read_text(encoding="utf-8"))) if args.config else Config()
        if args.command == "batch":
            results = []
            args.output.mkdir(parents=True, exist_ok=True)
            for mode in args.modes:
                for seed in args.seeds:
                    sim = Simulation(replace(config, mode=mode, seed=seed)).step(args.ticks)
                    result = summarize(sim)
                    results.append(result)
                    if args.full_runs:
                        export_run(sim, args.output / f"{mode}-seed-{seed}")
                    print(f"{mode:8} seed={seed:<5} population={result['final_population']:<5} {result['diagnosis']['status']}", flush=True)
            (args.output / "summary.json").write_text(json.dumps({"base_config": config.to_dict(), "results": results}, indent=2), encoding="utf-8")
            flat = [dict(seed=r["seed"], mode=r["mode"], ticks=r["ticks"], status=r["diagnosis"]["status"],
                         final_population=r["final_population"], peak_population=r["peak_population"], extinction_tick=r["extinction_tick"],
                         total_births=r["total_births"], total_deaths=r["total_deaths"], shortage_ticks=r["shortage_ticks"],
                         capacity_limit_reached=r["capacity_limit_reached"]) for r in results]
            with (args.output / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(flat[0]))
                writer.writeheader()
                writer.writerows(flat)
            print(f"Comparison saved to {args.output.resolve()}")
        else:
            if args.seed is not None:
                config = replace(config, seed=args.seed)
            if args.mode:
                config = replace(config, mode=args.mode)
            sim = load(args.resume) if args.resume else Simulation(config)
            if args.command == "run":
                sim.step(args.ticks)
                export_run(sim, args.output)
                print(json.dumps(summarize(sim), indent=2))
                print(f"Run saved to {args.output.resolve()}")
            else:
                from .server import serve
                serve(sim, args.port, not args.no_browser)
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Gaia: {exc}\n")
