#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  📈 LOC PLOTTER - Lines of Code Visualization           ║
║  "Watch your codebase grow!"                             ║
║                                                           ║
║  Reads loc-history.csv and generates a beautiful        ║
║  area plot showing your code growth over the last year. ║
╚══════════════════════════════════════════════════════════╝
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    print("📈 [ERROR] matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "loc-data"
DATA_FILE = DATA_DIR / "loc-history.csv"
OUTPUT_IMAGE = SCRIPT_DIR / "loc-chart.png"
DAYS_BACK = 365  # Last 1 year

# Chart styling
COLORS = {
    "bg": "#0d1117",          # GitHub dark background
    "grid": "#21262d",        # Grid lines
    "line_loc": "#58a6ff",    # Blue for LOC line
    "fill_loc": "#58a6ff",    # Blue fill
    "text": "#c9d1d9",        # Main text
    "text_dim": "#8b949e",    # Dimmed text
    "title": "#ffffff",       # Title
}

# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────
def load_data():
    """Load LOC data from CSV file."""
    if not DATA_FILE.exists():
        print(f"📈 [ERROR] Data file not found: {DATA_FILE}")
        print("Run locometer.sh first to generate data!")
        sys.exit(1)

    dates = []
    loc_values = []

    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date = datetime.strptime(row["date"], "%Y-%m-%d")
                dates.append(date)
                loc_values.append(int(row["total_loc"]))
            except (ValueError, KeyError) as e:
                print(f"📈 [WARN] Skipping invalid row: {e}")
                continue

    if not dates:
        print("📈 [ERROR] No valid data found in CSV file!")
        sys.exit(1)

    return dates, loc_values


def filter_last_year(dates, loc_values):
    """Filter data to only include the last year."""
    cutoff = datetime.now() - timedelta(days=DAYS_BACK)

    filtered_dates = []
    filtered_loc = []

    for d, loc in zip(dates, loc_values):
        if d >= cutoff:
            filtered_dates.append(d)
            filtered_loc.append(loc)

    return filtered_dates, filtered_loc


def create_plot(dates, loc_values):
    """Create the area plot."""
    # Setup figure
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    # ── Lines of Code ──
    ax.fill_between(
        dates, loc_values, alpha=0.2, color=COLORS["fill_loc"], linewidth=0
    )
    ax.plot(
        dates,
        loc_values,
        color=COLORS["line_loc"],
        linewidth=3,
        marker="o",
        markersize=8,
        label="Lines of Code",
        zorder=5,
    )
    ax.set_xlabel("Date", fontsize=13, color=COLORS["text"], fontweight="bold")
    ax.set_ylabel("Lines of Code", fontsize=14, color=COLORS["line_loc"], fontweight="bold")
    ax.tick_params(axis="x", colors=COLORS["text_dim"], labelsize=11)
    ax.tick_params(axis="y", colors=COLORS["line_loc"], labelsize=11)

    # ── Grid ──
    ax.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.5, alpha=0.5)

    # ── Title ──
    total_loc = loc_values[-1] if loc_values else 0
    growth = ""
    if len(loc_values) >= 2:
        diff = loc_values[-1] - loc_values[0]
        sign = "+" if diff >= 0 else ""
        growth = f"  |  Growth: {sign}{diff:,} LOC"

    title = f"🚂 Code Growth - Last {DAYS_BACK//30} Months  |  Total: {total_loc:,} LOC{growth}"
    fig.suptitle(
        title,
        fontsize=16,
        fontweight="bold",
        color=COLORS["title"],
        y=0.98,
    )

    # ── Date formatting ──
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # ── Legend ──
    ax.legend(
        loc="upper left",
        fontsize=11,
        framealpha=0.1,
        facecolor=COLORS["bg"],
        edgecolor=COLORS["grid"],
        labelcolor=COLORS["text"],
    )

    # ── Layout ──
    fig.tight_layout(pad=2.0)
    plt.subplots_adjust(top=0.88)

    return fig


def main():
    print("📈 ╔══════════════════════════════════════════╗")
    print("📈 ║     📈 LOC Plotter - Chart Generator    ║")
    print("📈 ╚══════════════════════════════════════════╝")
    print()

    # Load data
    print("📈 Loading data...")
    dates, loc_values = load_data()
    print(f"📈 Found {len(dates)} data points")

    # Filter to last year
    print(f"📈 Filtering to last {DAYS_BACK} days...")
    dates, loc_values = filter_last_year(dates, loc_values)
    print(f"📈 {len(dates)} data points in range")
    print()

    if len(dates) < 2:
        print("📈 [WARN] Only one data point found. Creating a single-point chart.")
        # Duplicate the point so matplotlib can render it
        dates = [dates[0], dates[0]]
        loc_values = [loc_values[0], loc_values[0]]

    # Create and save plot
    print("📈 Generating plot...")
    fig = create_plot(dates, loc_values)
    fig.savefig(
        OUTPUT_IMAGE,
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)

    print(f"📈 Chart saved to: {OUTPUT_IMAGE}")
    print()
    print("📈 To display in README.md, add this line:")
    print(f'📈   `![LOC Chart](./loc-chart.png)`')


if __name__ == "__main__":
    main()
