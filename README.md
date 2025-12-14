
# PAI Task 2 – Supermarket Purchasing Pattern Analysis

This project analyzes customer purchasing patterns using:
- **Co-occurrence detection** (item support, pair & trio counts)
- **Simple, fast queries**:
  - Top co-purchases for a given item
  - Top-N bundles (pairs & optional trios)
  - Quick pair check with support/confidence/lift
  - Graph-based recommendations (optional)
- **Visualizations**: bar charts, co-occurrence heatmap, and network graph

## CLI Menu
- [1] Top co‑purchases for an item
- [2] Top 3 most common bundles (pairs & trios)
- [3] Check if two items are often co‑purchased
- [4] Plot: Top co‑purchases (bar chart)
- [5] Plot: Top bundles (bar chart)
- [6] Plot: Co‑occurrence heatmap
- [7] Plot: Co‑occurrence network (thresholded)
- [0] Exit

## Project Structure

task_2/\
├─ README.md\
├─ requirements.txt\
├─ .gitignore\
├─ src/\       
│     ├─ __init__.py\
│     ├─ data_loader.py\
│     ├─ analytics.py          # co-occurrence cache + query functions\
│     ├─ visualization.py      # plotting helpers (bar charts, heatmap, graph)\
│     ├─ cli.py                # menu using the analytics functions\
│     └─ main.py\
└─ tests/\
   ├─ test_analytics.py\
   └─ test_visualization_smoke.py

## Setup

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt
pytest -q
```