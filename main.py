import argparse
import sys
from sensors.csv_sensor import CSVSensor
from agents.simple_reflex import SimpleReflexAgent
from agents.model_based import ModelBasedAgent
from environment import Environment
from plugins.logger import LoggerPlugin
from plugins.threshold_alert import ThresholdAlertPlugin
from config.pollutants import BREAKPOINTS
from visualizer import (
    plot_city_aqi_bar,
    plot_subindex_breakdown,
    plot_aqi_trend,
    plot_pollutant_heatmap,
)

RESET = "\033[0m"
BOLD  = "\033[1m"

CATEGORY_COLORS = {
    "Good":         "\033[32m",
    "Satisfactory": "\033[92m",
    "Moderate":     "\033[33m",
    "Poor":         "\033[93m",
    "Very Poor":    "\033[91m",
    "Severe":       "\033[35m",
    "Unknown":      "\033[90m",
}

BAR_WIDTH = 42

def _bar(aqi):
    filled = int((min(aqi, 500) / 500) * BAR_WIDTH)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + f"]  {aqi:.1f} / 500"

def print_result(sensor_data, action, label=""):
    meta = sensor_data.get("_meta", {})
    city = meta.get("City", meta.get("Station", ""))
    date = meta.get("Date", "")
    cat  = action["category"]
    col  = CATEGORY_COLORS.get(cat, "")
    print()
    print("=" * 62)
    if label:
        print(f"  Observation   : {label}")
    if city:
        print(f"  City          : {city}")
    if date:
        print(f"  Date          : {date}")
    print()
    print(f"  {BOLD}Sensor Readings{RESET}")
    for poll, conc in sensor_data.items():
        if poll.startswith("_"):
            continue
        unit   = BREAKPOINTS[poll]["unit"] if poll in BREAKPOINTS else ""
        si     = action["sub_indices"].get(poll)
        si_str = f"sub-index: {si:.1f}" if si is not None else "out of range"
        print(f"    {poll:<8}  {conc:>9.2f} {unit:<7}  ->  {si_str}")
    print()
    print(f"  {BOLD}AQI Result{RESET}")
    print(f"    {_bar(action['aqi'])}")
    print(f"    {col}{BOLD}{cat.upper()}  (AQI = {action['aqi']:.1f}){RESET}")
    print(f"    Dominant pollutant : {action['dominant']}")
    if action.get("trend"):
        print(f"    Trend              : {action['trend']}")
    if action.get("alert"):
        print(f"    {BOLD}\033[91m{action['alert']}{RESET}")
    print()
    print(f"  {BOLD}Advisory{RESET}")
    print(f"    {action['advisory']}")
    print("=" * 62)

def print_summary(results):
    print()
    print(f"  {'#':<4}  {'City':<14}  {'Date':<12}  {'AQI':>6}  {'Category':<14}  Dominant")
    print("  " + "-" * 66)
    for i, (sensor_data, action) in enumerate(results):
        meta = sensor_data.get("_meta", {})
        city = meta.get("City", "—")[:13]
        date = meta.get("Date", "—")[:11]
        aqi  = f"{action['aqi']:.1f}" if action["aqi"] is not None else "—"
        cat  = action["category"]
        dom  = action["dominant"] or "—"
        col  = CATEGORY_COLORS.get(cat, "")
        alert = " *" if action.get("alert") else ""
        print(f"  {i+1:<4}  {city:<14}  {date:<12}  {aqi:>6}  {col}{cat:<14}{RESET}  {dom}{alert}")
    print()

def main():
    parser = argparse.ArgumentParser(description="AQI Reflex Agent")
    parser.add_argument("--file",      default="data/city_day.csv")
    parser.add_argument("--row",       type=int, default=-1)
    parser.add_argument("--all",       action="store_true")
    parser.add_argument("--agent",     default="simple", choices=["simple", "model"])
    parser.add_argument("--visualize", action="store_true")
    parser.add_argument("--log",       action="store_true")
    parser.add_argument("--alert",     type=int, default=None)
    parser.add_argument("--output",    default="output")
    args = parser.parse_args()

    sensor = CSVSensor()
    agent  = SimpleReflexAgent() if args.agent == "simple" else ModelBasedAgent()
    plugins = []
    if args.log:
        plugins.append(LoggerPlugin(log_file=f"{args.output}/aqi_log.csv"))
    if args.alert is not None:
        plugins.append(ThresholdAlertPlugin(threshold=args.alert))

    env = Environment(sensor=sensor, source=args.file, plugins=plugins)

    print()
    print(f"{BOLD}{'=' * 62}")
    print("  AQI REFLEX AGENT")
    print(f"  Agent: {args.agent.title()}  |  India CPCB Methodology  |  SIM-46-2021")
    print(f"{'=' * 62}{RESET}")
    print(f"  Dataset   : {args.file}")

    if args.all:
        print("  Mode      : Batch\n")
        results = env.run_all(agent)
        if not results:
            print("  ERROR: No usable rows found.")
            sys.exit(1)
        print_summary(results)

        worst = max(results, key=lambda x: x[1]["aqi"] or 0)
        best  = min(results, key=lambda x: x[1]["aqi"] or 999)
        print(f"  {BOLD}Worst observation:{RESET}")
        print_result(worst[0], worst[1], label="Highest AQI")
        print(f"  {BOLD}Best observation:{RESET}")
        print_result(best[0], best[1], label="Lowest AQI")

        if args.alert is not None:
            alert_plugin = next((p for p in plugins if hasattr(p, "alerts")), None)
            if alert_plugin and alert_plugin.alerts:
                print(f"\n  {BOLD}Threshold Alerts (AQI > {args.alert}):{RESET}")
                for a in alert_plugin.alerts:
                    print(f"    {a['city']:<14}  {a['date']:<12}  AQI: {a['aqi']:.1f}  ({a['category']})")

        if args.visualize:
            print(f"\n  Generating visualizations -> {args.output}/")
            print(f"    Saved: {plot_city_aqi_bar(results, args.output)}")
            print(f"    Saved: {plot_pollutant_heatmap(results, args.output)}")
            cities_seen = set()
            for sensor_data, _ in results:
                city = sensor_data.get("_meta", {}).get("City", "")
                if city and city not in cities_seen:
                    path = plot_aqi_trend(results, city, args.output)
                    if path:
                        print(f"    Saved: {path}")
                    cities_seen.add(city)
            path = plot_subindex_breakdown(worst[0], worst[1], args.output)
            if path:
                print(f"    Saved: {path}")
            print(f"\n  All plots saved to ./{args.output}/")
    else:
        row_label = "latest row" if args.row == -1 else f"row {args.row}"
        print(f"  Mode      : Single ({row_label})\n")
        sensor_data, action = env.step(agent, row_index=args.row)
        print_result(sensor_data, action, label=row_label)
        if args.visualize:
            path = plot_subindex_breakdown(sensor_data, action, args.output)
            if path:
                print(f"\n  Saved: {path}")

if __name__ == "__main__":
    main()
