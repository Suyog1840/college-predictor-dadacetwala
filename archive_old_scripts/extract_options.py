import pandas as pd
import json

# Load necessary data
trend_df = pd.read_excel("output/trend_table.xlsx")
college_meta = pd.read_excel("college_meta.xlsx")
try:
    branch_names = pd.read_csv("output/branch_names.csv")
    branch_names = branch_names.drop_duplicates(subset=["branchCode"])
except FileNotFoundError:
    branch_names = pd.DataFrame(columns=["branchCode", "branchName"])

# Merge data similar to simulation engine
df = trend_df.merge(college_meta, on="collegeCode", how="left")
df = df.merge(branch_names, on="branchCode", how="left")

# Helper to extract and sort by value counts
def get_sorted_options_by_frequency(series):
    # Get counts of each unique value, drop NA, convert index to string, and return as a list
    return [str(x) for x in series.dropna().value_counts().index.tolist()]

# 1. District Options
districts = get_sorted_options_by_frequency(df["district"])

# 2. Home University Options
universities = get_sorted_options_by_frequency(df["homeUniversity"])

# 3. Branch Options
branches = get_sorted_options_by_frequency(df["branchName"])

# 4. Category Options
# baseCategory in trend data is like AI, GOPEN, LOPEN, TFWS, GOBC, LOBC, etc.
# But for the student input, the categories are OPEN, OBC, SC, ST, VJ, NT1, NT2, NT3, TFWS
# We can extract the base parts and keep a count of each underlying category mapping
raw_categories_counts = df["baseCategory"].dropna().value_counts()
valid_categories_counts = {}

for cat, count in raw_categories_counts.items():
    cat = str(cat)
    mapped_cat = None
    if cat in ["AI", "GOPEN", "LOPEN", "TFWS"]:
        if cat in ["GOPEN", "LOPEN"]:
            mapped_cat = "OPEN"
        elif cat == "TFWS":
            mapped_cat = "TFWS"
    elif cat.startswith("G") or cat.startswith("L"):
        mapped_cat = cat[1:]
        
    if mapped_cat:
        valid_categories_counts[mapped_cat] = valid_categories_counts.get(mapped_cat, 0) + count

# Sort the categories by the accumulated counts descending
categories = [cat for cat, _ in sorted(valid_categories_counts.items(), key=lambda item: item[1], reverse=True)]

options = {
    "categories": categories,
    "districts": districts,
    "homeUniversities": universities,
    "branches": branches
}

with open("frontend_options.json", "w") as f:
    json.dump(options, f, indent=4)

print("Extracted options successfully to frontend_options.json")
