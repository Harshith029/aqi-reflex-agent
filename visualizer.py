import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

CATEGORY_COLORS = {
    "Good":         "#4caf50",
    "Satisfactory": "#8bc34a",
    "Moderate":     "#ffc107",
    "Poor":         "#ff9800",
    "Very Poor":    "#f44336",
    "Severe":       "#9c27b0",
    "Unknown":      "#9e9e9e",
}

AQI_BANDS = [(0,50,"#4caf50"), (51,100,"#8bc34a"), (101,200,"#ffc107"),
             (201,300,"#ff9800"), (301,400,"#f44336"), (401,500,"#9c27b0")]

def _category_for_aqi(aqi):
    for lo, hi, label in [(0,50,"Good"),(51,100,"Satisfactory"),(101,200,"Moderate"),
                          (201,300,"Poor"),(301,400,"Very Poor"),(401,500,"Severe")]:
        if lo <= aqi <= hi:
            return label
    return "Severe"

def _base_style(fig, ax):
    fig.patch.set_facecolor("#f9f9f9")
    ax.set_facecolor("#f9f9f9")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(axis="both", colors="#444444")

def plot_city_aqi_bar(batch_results, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    cities = {}
    for sensor_data, action in batch_results:
        city = sensor_data.get("_meta", {}).get("City", "Unknown")
        if action["aqi"] is not None:
            cities.setdefault(city, []).append(action["aqi"])
    city_avg     = {c: np.mean(v) for c, v in cities.items() if v}
    sorted_items = sorted(city_avg.items(), key=lambda x: x[1], reverse=True)
    names  = [c for c, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors = [CATEGORY_COLORS[_category_for_aqi(v)] for v in values]
    fig, ax = plt.subplots(figsize=(12, 6))
    _base_style(fig, ax)
    bars = ax.barh(names, values, color=colors, height=0.55, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax.text(val + 4, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", ha="left", fontsize=10, color="#333333")
    for lo, hi, color in AQI_BANDS:
        ax.axvspan(lo, hi, alpha=0.06, color=color, zorder=0)
    ax.set_xlim(0, 520)
    ax.set_xlabel("Average AQI", fontsize=11, color="#444444", labelpad=8)
    ax.set_title("Average AQI by City  |  India CPCB Scale", fontsize=13,
                 fontweight="bold", color="#222222", pad=14)
    patches = [mpatches.Patch(color=CATEGORY_COLORS[cat], label=cat)
               for cat in ["Good","Satisfactory","Moderate","Poor","Very Poor","Severe"]]
    ax.legend(handles=patches, loc="lower right", fontsize=8, framealpha=0.7, edgecolor="#cccccc")
    plt.tight_layout()
    path = os.path.join(output_dir, "city_aqi_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path

def plot_subindex_breakdown(sensor_data, action, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    sub_indices = action["sub_indices"]
    if not sub_indices:
        return None
    pollutants = list(sub_indices.keys())
    values     = [sub_indices[p] for p in pollutants]
    colors     = [CATEGORY_COLORS[_category_for_aqi(v)] for v in values]
    fig, ax    = plt.subplots(figsize=(10, 5))
    _base_style(fig, ax)
    x    = np.arange(len(pollutants))
    bars = ax.bar(x, values, color=colors, width=0.55, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 5,
                f"{val:.0f}", ha="center", va="bottom", fontsize=9, color="#333333")
    for lo, hi, color in AQI_BANDS:
        ax.axhspan(lo, hi, alpha=0.06, color=color, zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(pollutants, fontsize=10)
    ax.set_ylim(0, 530)
    ax.set_ylabel("Sub-Index", fontsize=11, color="#444444", labelpad=8)
    meta  = sensor_data.get("_meta", {})
    city  = meta.get("City", "")
    date  = meta.get("Date", "")
    title = "Pollutant Sub-Index Breakdown"
    if city:
        title += f"  |  {city}"
    if date:
        title += f"  ({date})"
    ax.set_title(title, fontsize=12, fontweight="bold", color="#222222", pad=12)
    ax.axhline(y=action["aqi"], color="#333333", linestyle="--", linewidth=1.2,
               label=f"Final AQI = {action['aqi']:.1f}")
    ax.legend(fontsize=9, framealpha=0.7, edgecolor="#cccccc")
    plt.tight_layout()
    city_slug = city.lower().replace(" ", "_") if city else "observation"
    path = os.path.join(output_dir, f"subindex_{city_slug}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path

def plot_aqi_trend(batch_results, city_name, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    dates, values = [], []
    for sensor_data, action in batch_results:
        meta = sensor_data.get("_meta", {})
        if meta.get("City", "") == city_name and action["aqi"] is not None:
            dates.append(meta.get("Date", str(len(dates))))
            values.append(action["aqi"])
    if len(values) < 2:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    _base_style(fig, ax)
    for lo, hi, color in AQI_BANDS:
        ax.axhspan(lo, hi, alpha=0.08, color=color)
    ax.plot(dates, values, color="#1a1a2e", linewidth=2, marker="o",
            markersize=6, markerfacecolor="white", markeredgewidth=2)
    for d, v in zip(dates, values):
        ax.annotate(f"{v:.0f}", (d, v), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=8, color="#333333")
    ax.set_title(f"AQI Trend  |  {city_name}", fontsize=12,
                 fontweight="bold", color="#222222", pad=12)
    ax.set_ylabel("AQI", fontsize=11, color="#444444")
    ax.set_ylim(0, 530)
    plt.tight_layout()
    path = os.path.join(output_dir, f"trend_{city_name.lower().replace(' ','_')}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path

def plot_pollutant_heatmap(batch_results, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    import pandas as pd
    from aqi_calculator import sub_index
    from config.pollutants import BREAKPOINTS
    pollutants = list(BREAKPOINTS.keys())
    rows = []
    for sensor_data, action in batch_results:
        meta  = sensor_data.get("_meta", {})
        label = f"{meta.get('City','?')} ({meta.get('Date','')})"
        row   = {"label": label}
        for p in pollutants:
            conc    = sensor_data.get(p)
            row[p]  = sub_index(p, conc) if conc is not None else np.nan
        rows.append(row)
    df  = pd.DataFrame(rows).set_index("label")[pollutants]
    fig, ax = plt.subplots(figsize=(14, max(6, len(df) * 0.45)))
    fig.patch.set_facecolor("#f9f9f9")
    data = df.values
    im   = ax.imshow(data, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=500)
    ax.set_xticks(np.arange(len(pollutants)))
    ax.set_xticklabels(pollutants, fontsize=10)
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(df.index, fontsize=8)
    for i in range(len(df)):
        for j in range(len(pollutants)):
            val = data[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=7.5, color="black" if val < 300 else "white")
    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("Sub-Index", fontsize=10, color="#444444")
    cbar.ax.tick_params(labelsize=8)
    ax.set_title("Pollutant Sub-Index Heatmap  |  All Observations",
                 fontsize=12, fontweight="bold", color="#222222", pad=12)
    plt.tight_layout()
    path = os.path.join(output_dir, "heatmap_all.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path
