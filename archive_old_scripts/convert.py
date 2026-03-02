import pandas as pd

# ----------------------------
# LOAD ORIGINAL FILE
# ----------------------------
input_file = "CollegeDetails_rows.csv"
output_file = "college_meta.xlsx"

df = pd.read_csv(input_file)

# ----------------------------
# CLEAN COLUMN NAMES
# ----------------------------
df.columns = df.columns.str.strip()

# Ensure required columns exist
required_cols = ["collegeCode", "collegeName", "homeUniversity", "district"]

missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise Exception(f"Missing required columns: {missing}")

# ----------------------------
# MARK WOMEN'S COLLEGES
# ----------------------------
def is_women_college(name):
    name = str(name).lower()

    keywords = [
        "women",
        "women's",
        "girls",
        "mahila"
        "Women",  
        "Women's",
        "Women,"  
    ]

    return any(keyword in name for keyword in keywords)

df["isWomenCollege"] = df["collegeName"].apply(is_women_college)

# ----------------------------
# SELECT FINAL META COLUMNS
# ----------------------------
college_meta = df[
    ["collegeCode", "collegeName", "homeUniversity", "district", "isWomenCollege"]
].copy()

# Ensure collegeCode is string
college_meta["collegeCode"] = college_meta["collegeCode"].astype(str)

# ----------------------------
# SAVE
# ----------------------------
college_meta.to_excel(output_file, index=False)

print("College meta file generated:", output_file)
print("Total colleges:", len(college_meta))
print("Women's colleges detected:", college_meta["isWomenCollege"].sum())