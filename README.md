
# PAI Task 2 – Supermarket Purchasing Pattern Analysis

This project analyzes customer purchasing patterns using:
- **Co-occurrence detection** (item support, pair & trio counts)
- **Simple, fast queries**:
  - Top co-purchases for a given item
  - Top-N bundles (pairs & optional trios)
  - Quick pair check with support/confidence/lift metrics
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

**Note** 
1. Enter items in lower case only
2. Explanation for CLI Menu option 3
    - Prompts for two items (Item A and Item B) with case-sensitive matching and warnings if items aren't found
    - Asks for thresholds:
      - Minimum count (default 5): how many transactions must contain both items
      - Minimum support (default 0.01): the fraction of all transactions containing the pair
    - Displays basic metrics:
      - Count(A,B): absolute number of times both appear together
      - Support(A,B): percentage of transactions with both items
      - Often?: YES/NO answer—whether the pair meets your thresholds  
    - Optional detailed view: If user wants more depth, shows:
      - Confidence A→B: likelihood of B given A was purchased
      - Confidence B→A: likelihood of A given B was purchased
      - Lift: how much more likely they're bought together vs. independently  

## Project Structure

```
task_2/
├── 📄 README.md                          # User guide & setup instructions
├── 📄 requirements.txt                   # Python package dependencies
├── 📄 Supermarket_dataset_PAI.csv        # Input transaction data (14,963 transactions)
├── 📄 benchmark_complexity.py            # Empirical complexity validation script
│
├── 📁 src/                               # Main package
│   ├── __init__.py                       # Package metadata
│   ├── main.py                           # Entry point
│   ├── cli.py                            # Interactive CLI menu (7 options)
│   ├── data_loader.py                    # CSV input with auto-detected columns
│   ├── analytics.py                      # Core analysis (cache, queries)
│   └── visualization.py                  # Plotting (bar, heatmap, network)
│                       
│
└── 📁 tests/                             # Test suite (5 tests, 100% pass)
    ├── test_analytics.py                 # Cache & query function tests
    └── test_visualization_smoke.py       # Plot generation smoke tests
    

```

## Setup & Installation

### 1. Create Virtual Environment
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -r requirements.txt
pytest -q
```
## To run CLI Menu

```bash
python -m src.main Supermarket_dataset_PAI.csv
```
## To run Benchmark Tests
```bash
python benchmark_complexity.py
```