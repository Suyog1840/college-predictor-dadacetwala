import pandas as pd
import math

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_DATA_DIR = os.path.join(BASE_DIR, "..", "deployment_data")

# -----------------------------------
# LOAD DATA
# -----------------------------------
trend_df = pd.read_excel(os.path.join(DEPLOY_DATA_DIR, "trend_table.xlsx"))
college_meta = pd.read_excel(os.path.join(DEPLOY_DATA_DIR, "college_meta.xlsx"))
try:
    branch_names = pd.read_csv(os.path.join(DEPLOY_DATA_DIR, "branch_names.csv"))
    branch_names = branch_names.drop_duplicates(subset=["branchCode"])
except FileNotFoundError:
    branch_names = pd.DataFrame(columns=["branchCode", "branchName"])

trend_df = trend_df.merge(college_meta, on="collegeCode", how="left")
trend_df = trend_df.merge(branch_names, on="branchCode", how="left")

# Convert TRUE/FALSE strings to real boolean
trend_df["isWomenCollege"] = (
    trend_df["isWomenCollege"]
    .astype(str)
    .str.upper()
    .map({"TRUE": True, "FALSE": False})
    .fillna(False)
)




# -----------------------------------
# HELPER
# -----------------------------------
def sigmoid(x):
    # Adjusted sigmoid to create more generous spreads for probabilities
    # A margin of -3 gives ~23%, -1 gives ~60%, 0 gives 76%, +2 gives 94%
    return 1 / (1 + math.exp(-0.8 * (x + 1.5)))


# -----------------------------------
# MAIN PREDICTION FUNCTION
# -----------------------------------
def predict(student):

    scores = student.get("scores", {})
    category = student["category"]
    gender = student["gender"]
    homeUni = student["homeUniversity"]
    preferredBranches = student["branchPreference"]
    preferredDistricts = student["districtPreference"]



    all_results = []
    
    for examType, percentile in scores.items():
        df = trend_df.copy()

        # ---------------- EXAM FILTER ----------------
        df = df[df["examType"] == examType]


        # ---------------- DISTRICT FILTER ----------------
        if preferredDistricts:
            df = df[df["district"].isin(preferredDistricts)]


        # ---------------- GENDER FILTER ----------------
        if gender == "Male":
            df = df[
                (~df["isWomenCollege"]) &
                (~df["branchCode"].astype(str).str.endswith("L"))
            ]

        # ---------------- SEATFLAG FILTER ----------------
        def seat_flag_valid(row):
            if row["seatFlag"] == "H":
                return row["homeUniversity"] == homeUni
            elif row["seatFlag"] == "O":
                return row["homeUniversity"] != homeUni
            else:
                return True

        df = df[df.apply(seat_flag_valid, axis=1)]


        # ---------------- GROUP BY BRANCH ----------------
        grouped = df.groupby(["collegeCode", "branchCode"])

        for (collegeCode, branchCode), group in grouped:

            branchName = group.iloc[0]["branchName"]

            # Branch preference filter
            if preferredBranches:
                if branchName not in preferredBranches:
                    continue

            # Compute standard intrinsic cutoff value (GOPEN/AI) for ranking
            standard_cutoff = 0
            if examType == "JEE":
                std_row = group[group["baseCategory"] == "AI"]
            else:
                std_row = group[group["baseCategory"] == "GOPEN"]
                
            if not std_row.empty:
                standard_cutoff = std_row.iloc[0]["weighted_cutoff"]
            else:
                # Fallback if standard category is somehow missing in this block
                standard_cutoff = group["weighted_cutoff"].max()

            valid_categories = []
            if examType == "JEE":
                valid_categories = ["AI"]
            else:
                valid_categories = []
                
                # If they explicitly opted into TFWS category
                if category == "TFWS":
                    valid_categories.append("TFWS")
                    
                valid_categories.append("GOPEN")
                
                if gender == "Female":
                    valid_categories.append("LOPEN")
                
                if category != "OPEN" and category != "TFWS":
                    valid_categories.append(f"G{category}")
                    if gender == "Female":
                        valid_categories.append(f"L{category}")

            best_option = None
            best_adj_margin = -9999.0

            for cat_name in valid_categories:
                cat_row = group[group["baseCategory"] == cat_name]
                if not cat_row.empty:
                    candidate = cat_row.iloc[0]
                    margin = percentile - candidate["weighted_cutoff"]
                    # Allow up to -8 margin so reach colleges are included;
                    # the sigmoid will assign them a lower probability naturally.
                    if margin >= -8:
                        adj_margin = margin - (candidate["trend_slope"] * 0.5)
                        if adj_margin > best_adj_margin:
                            best_adj_margin = adj_margin
                            best_option = candidate

            if best_option is None or "collegeCode" not in best_option:
                continue

            # ---------------- PROBABILITY ----------------
            margin = percentile - best_option["weighted_cutoff"]
            
            # Constrain the slope to prevent extreme outliers skewing the probability
            bounded_slope = max(-2.0, min(2.0, best_option["trend_slope"]))
            
            # Penalize the margin based on historical volatility (higher SD = less certain)
            volatility_penalty = best_option["volatility"] * 0.2
            
            adjusted_margin = margin - (bounded_slope * 0.4) - volatility_penalty
            probability = sigmoid(adjusted_margin)

            all_results.append({
                "examType": str(examType),
                "collegeCode": int(best_option["collegeCode"]),
                "collegeName": str(best_option["collegeName"]),
                "branchCode": str(best_option["branchCode"]),
                "branchName": str(best_option["branchName"]) if best_option["branchName"] == best_option["branchName"] else "",
                "district": str(best_option["district"]) if best_option["district"] == best_option["district"] else "",
                "weighted_cutoff": float(best_option["weighted_cutoff"]),
                "standard_cutoff": float(standard_cutoff),
                "probability": round(float(probability) * 100, 2)
            })

    # ---------------- FILTER BY PROBABILITY ----------------
    # Keep anything with at least 45% chance - this includes good reach colleges.
    # Too high a threshold (e.g. 60-70%) would only show the easiest/worst colleges.
    all_results = [r for r in all_results if r["probability"] >= 45.0]

    # ---------------- SORT BY PRESTIGE (standard_cutoff) ----------------
    # Sort by standard_cutoff DESCENDING so the most prestigious/competitive colleges
    # come first. Use probability as a tiebreaker within similar prestige tiers.
    # This ensures we surface the BEST colleges the student can realistically get,
    # not just the safest/easiest ones.
    all_results.sort(
        key=lambda x: (x["standard_cutoff"], x["probability"]),
        reverse=True
    )

    # ---------------- DEDUPLICATE ----------------
    # Filter combinations of college name and branch name, keeping the highest ranked one
    seen_combos = set()
    deduped_results = []
    
    for r in all_results:
        combo_key = (r["collegeName"], r["branchName"])
        if combo_key not in seen_combos:
            seen_combos.add(combo_key)
            deduped_results.append(r)

    # ---------------- TIERED SELECTION ----------------
    # Build a balanced top-5 across reach (45-65%), target (65-85%), and safe (85%+) tiers.
    # This ensures students see aspirational colleges alongside safe bets.
    reach   = [r for r in deduped_results if r["probability"] < 65.0]
    target  = [r for r in deduped_results if 65.0 <= r["probability"] < 85.0]
    safe    = [r for r in deduped_results if r["probability"] >= 85.0]

    final = []
    # Fill up to 5: prioritise target → safe → reach (best colleges in each tier first)
    for pool in [target, safe, reach]:
        for r in pool:
            if len(final) >= 5:
                break
            combo_key = (r["collegeName"], r["branchName"])
            if combo_key not in {(x["collegeName"], x["branchName"]) for x in final}:
                final.append(r)
        if len(final) >= 5:
            break

    # If we still have fewer than 5, top up from whatever remains
    if len(final) < 5:
        for r in deduped_results:
            if len(final) >= 5:
                break
            combo_key = (r["collegeName"], r["branchName"])
            if combo_key not in {(x["collegeName"], x["branchName"]) for x in final}:
                final.append(r)

    return final


# -----------------------------------
# TEST EXECUTION
# -----------------------------------
if __name__ == "__main__":
    student = {
        "scores": {
            "MHTCET": 92.0,
            "JEE": 60.0
        },
        "category": "NT2",
        "gender": "Male",
        "homeUniversity": "Savitribai Phule Pune University",
        "branchPreference": [
            "Electrical Engineering",
        ],
        "districtPreference": ["Pune"]
    }

    predictions = predict(student)

    print("\n--- Overall Top 5 Matches ---")
    if not predictions:
        print("No matches found.")
    for r in predictions:
        print(f"[{r['examType']}] College: {r['collegeName']}, Branch: {r['branchName']}, Prob: {r['probability']}%")