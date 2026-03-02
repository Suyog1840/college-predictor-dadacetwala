import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.linear_model import LinearRegression

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "..", "archive_old_data", "master_cutoff_data.xlsx")
OUTPUT_FILE = os.path.join(BASE_DIR, "..", "deployment_data", "trend_table.xlsx")

# -----------------------
# Load Master Dataset
# -----------------------
df = pd.read_excel(INPUT_FILE)

# -----------------------
# Extract baseCategory + seatFlag
# -----------------------
def split_category(cat):
    cat = str(cat)

    if cat.endswith("H"):
        return cat[:-1], "H"
    elif cat.endswith("O"):
        return cat[:-1], "O"
    elif cat.endswith("S"):
        return cat[:-1], "S"
    else:
        return cat, "NA"

df[["baseCategory", "seatFlag"]] = df["category"].apply(
    lambda x: pd.Series(split_category(x))
)

# -----------------------
# Prepare group keys
# -----------------------
group_cols = [
    "collegeCode",
    "branchCode",
    "examType",
    "baseCategory",
    "seatFlag",
    "round"  # Added round column for deeper granularity
]

def get_weight(year, round_num, is_latest_year=False):
    # Base weight by year, increasing exponentially to prioritize recent years
    base = {
        2022: 0.05,
        2023: 0.15,
        2024: 0.30,
        2025: 0.50,
        2026: 0.80  # Placeholder for future mid-year drops
    }.get(year, 0.05)
    
    # Modifier by round: Later rounds get higher priority as they reflect final cutoffs
    if is_latest_year:
        round_multiplier = {
            1: 0.5, 
            2: 0.8,
            3: 1.2,
            4: 1.5
        }.get(round_num, 1.5)
    else:
        round_multiplier = {
            1: 0.6, 
            2: 0.8,
            3: 0.9,
            4: 1.0
        }.get(round_num, 1.0)
    
    return base * round_multiplier

trend_rows = []

for keys, group in df.groupby(group_cols):

    group = group.sort_values("year")

    years = group["year"].values.reshape(-1, 1)
    cutoffs = group["closingPercentile"].values

    if len(cutoffs) < 2:
        continue

    weights_list = []
    
    weighted_sum = 0
    total_weight = 0

    for y, r, c in zip(group["year"], group["round"], cutoffs):
        latest_year = group["year"].max()
        w = get_weight(y, r, is_latest_year=(y == latest_year))
        weighted_sum += c * w
        total_weight += w
        weights_list.append(w)

    weighted_cutoff = weighted_sum / total_weight if total_weight > 0 else cutoffs[-1]

    # -----------------------
    # Trend slope (Linear Regression)
    # -----------------------
    model = LinearRegression()
    model.fit(years, cutoffs)
    slope = model.coef_[0]

    # -----------------------
    # Volatility
    # -----------------------
    volatility = np.std(cutoffs)

    trend_rows.append({
        "collegeCode": keys[0],
        "branchCode": keys[1],
        "examType": keys[2],
        "baseCategory": keys[3],
        "seatFlag": keys[4],
        "round_captured": keys[5],
        "weighted_cutoff": weighted_cutoff,
        "trend_slope": slope,
        "volatility": volatility
    })

trend_df = pd.DataFrame(trend_rows)

Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
trend_df.to_excel(OUTPUT_FILE, index=False)

print("Trend table generated:", OUTPUT_FILE)
print("Total trend rows:", len(trend_df))