import pdfplumber
import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# ---------------- CONFIG ----------------
AI_FOLDER = "AiPDFs"
OUTPUT_FILE = "output/ai_master_cutoff_data.xlsx"
# ----------------------------------------

rows = []

rank_pattern = re.compile(r"(\d+)\s*\(([\d.]+)\)")


# ---------- YEAR + ROUND ----------
def extract_year_round(filename):
    name = filename.lower()

    year_match = re.search(r"(20\d{2})", name)
    if not year_match:
        return None, None

    year = int(year_match.group(1))

    round_match = re.search(r"(r|round|cap)(\d+)", name)
    round_num = int(round_match.group(2)) if round_match else 1

    return year, round_num


# =====================================================
# =================== AI PDFs =========================
# =====================================================
for pdf_path in Path(AI_FOLDER).glob("*.pdf"):

    year, round_num = extract_year_round(pdf_path.name)
    if year is None:
        continue

    print(f"\nProcessing AI PDF: {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages, desc="AI Pages", leave=False):

            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:

                if not table or len(table) < 2:
                    continue

                header = table[0]

                # Skip non-AI tables
                if not any("Merit" in str(col) for col in header if col):
                    continue

                for row in table[1:]:

                    try:
                        sr_no = row[0]
                        merit_cell = row[1]
                        choice_code = row[2]
                        institute_cell = row[3]
                        course_name = row[4]

                        if not merit_cell or not choice_code or not institute_cell:
                            continue

                        # Extract rank + percentile
                        merit_match = rank_pattern.search(str(merit_cell))
                        if not merit_match:
                            continue

                        rank = int(merit_match.group(1))
                        percentile = float(merit_match.group(2))

                        # Extract college code + name
                        college_match = re.match(r"(\d{4,5})\s*-\s*(.+)", str(institute_cell))
                        if not college_match:
                            continue

                        college_code = college_match.group(1)
                        college_name = college_match.group(2).strip()

                        rows.append({
                            "year": year,
                            "round": round_num,
                            "examType": "JEE",
                            "quotaType": "ALL_INDIA",
                            "seatAllocationType": "ALL_INDIA",
                            "collegeCode": college_code,
                            "collegeName": college_name,
                            "branchCode": str(choice_code),
                            "branchName": str(course_name).strip(),
                            "category": "AI",
                            "closingRank": rank,
                            "closingPercentile": percentile
                        })

                    except Exception:
                        continue


# =====================================================
# =================== SAVE ============================
# =====================================================
df = pd.DataFrame(rows)

print("\nTotal AI Rows:", len(df))
print("\nRows Per Year:")
print(df.groupby("year").size())

Path("output").mkdir(exist_ok=True)

if Path(OUTPUT_FILE).exists():
    Path(OUTPUT_FILE).unlink()

wb = Workbook()
ws = wb.active
ws.title = "AI_MasterData"

for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

wb.save(OUTPUT_FILE)

print("✅ AI MASTER DATA GENERATED:", OUTPUT_FILE)