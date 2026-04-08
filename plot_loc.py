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
    "line_files": "#3fb950",  # Green for files line
    "fill_files": "#3fb950",  # Green fill
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
    file_values = []

    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date = datetime.strptime(row["date"], "%Y-%m-%d")
                dates.append(date)
                loc_values.append(int(row["total_loc"]))
                file_values.append(int(row["total_files"]))
            except (ValueError, KeyError) as e:
                print(f"📈 [WARN] Skipping invalid row: {e}")
                continue

    if not dates:
        print("📈 [ERROR] No valid data found in CSV file!")
        sys.exit(1)

    return dates, loc_values, file_values


def filter_last_year(dates, loc_values, file_values):
    """Filter data to only include the last year."""
    cutoff = datetime.now() - timedelta(days=DAYS_BACK)
    
    filtered_dates = []
    filtered_loc = []
    filtered_files = []
    
    for d, loc, files in zip(dates, loc_values, file_values):
        if d >= cutoff:
            filtered_date = d
            filtered_dates.append(filtered_date)
            filtered_loc.append(loc)
            filtered_files.append(files)
    
    return filtered_dates, filtered_loc, filtered_files


def create_plot(dates, loc_values, file_values):
    """Create the area plot."""
    # Setup figure
    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax1.set_facecolor(COLORS["bg"])

    # ── Primary Y-axis: Lines of Code ──
    ax1.fill_between(
        dates, loc_values, alpha=0.15, color=COLORS["fill_loc"], linewidth=0
    )
    ax1.plot(
        dates,
        loc_values,
        color=COLORS["line_loc"],
        linewidth=2.5,
        marker="o",
        markersize=6,
        label="Lines of Code",
        zorder=5,
    )
    ax1.set_xlabel("Date", fontsize=13, color=COLORS["text"], fontweight="bold")
    ax1.set_ylabel("Lines of Code", fontsize=13, color=COLORS["line_loc"], fontweight="bold")
    ax1.tick_params(axis="x", colors=COLORS["text_dim"], labelsize=11)
    ax1.tick_params(axis="y", colors=COLORS["line_loc"], labelsize=11)

    # ── Secondary Y-axis: Total Files ──
    ax2 = ax1.twinx()
    ax2.fill_between(
        dates, file_values, alpha=0.1, color=COLORS["fill_files"], linewidth=0
    )
    ax2.plot(
        dates,
        file_values,
        color=COLORS["line_files"],
        linewidth=2,
        marker="s",
        markersize=5,
        label="Total Files",
        linestyle="--",
        zorder=4,
    )
    ax2.set_ylabel(
        "Total Files", fontsize=13, color=COLORS["line_files"], fontweight="bold"
    )
    ax2.tick_params(axis="y", colors=COLORS["line_files"], labelsize=11)

    # ── Grid ──
    ax1.grid(True, color=COLORS["grid"], linestyle="-", linewidth=0.5, alpha=0.5)

    # ── Title ──
    total_loc = loc_values[-1] if loc_values else 0
    total_files = file_values[-1] if file_values else 0
    growth = ""
    if len(loc_values) >= 2:
        diff = loc_values[-1] - loc_values[0]
        sign = "+" if diff >= 0 else ""
        growth = f"  |  Growth: {sign}{diff:,} LOC"

    title = f"🚂 Code Growth - Last {DAYS_BACK//30} Months  |  Total: {total_loc:,} LOC  |  {total_files:,} Files{growth}"
    fig.suptitle(
        title,
        fontsize=16,
        fontweight="bold",
        color=COLORS["title"],
        y=0.98,
    )

    # ── Date formatting ──
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # ── Legend ──
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
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
    dates, loc_values, file_values = load_data()
    print(f"📈 Found {len(dates)} data points")

    # Filter to last year
    print(f"📈 Filtering to last {DAYS_BACK} days...")
    dates, loc_values, file_values = filter_last_year(dates, loc_values, file_values)
    print(f"📈 {len(dates)} data points in range")
    print()

    if len(dates) < 2:
        print("📈 [WARN] Only one data point found. Creating a single-point chart.")
        # Duplicate the point so matplotlib can render it
        dates = [dates[0], dates[0]]
        loc_values = [loc_values[0], loc_values[0]]
        file_values = [file_values[0], file_values[0]]

    # Create and save plot
    print("📈 Generating plot...")
    fig = create_plot(dates, loc_values, file_values)
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
