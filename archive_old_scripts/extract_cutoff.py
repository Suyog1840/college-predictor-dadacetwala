import pdfplumber
import pandas as pd
import re
from tqdm import tqdm
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# ---------------- CONFIG ----------------
STATE_FOLDER = "StatePDFs"
AI_FOLDER = "AiPDFs"
OUTPUT_FILE = "output/master_cutoff_data.xlsx"
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


# ---------- SEAT BLOCK DETECTOR ----------
def detect_seat_block(text):
    text = text.lower()

    if "home university seats allotted to home university candidates" in text:
        return "HOME_TO_HOME"
    if "home university seats allotted to other than home university candidates" in text:
        return "HOME_TO_OTHER"
    if "other than home university seats allotted to home university candidates" in text:
        return "OTHER_TO_HOME"
    if "other than home university seats allotted to other than home university candidates" in text:
        return "OTHER_TO_OTHER"
    if "state level" in text:
        return "STATE_LEVEL"

    return "UNKNOWN"


# =====================================================
# =================== STATE PDFs ======================
# =====================================================
for pdf_path in Path(STATE_FOLDER).glob("*.pdf"):

    year, round_num = extract_year_round(pdf_path.name)
    if year is None:
        continue

    print(f"\nProcessing STATE PDF: {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages, desc="STATE Pages", leave=False):

            text = page.extract_text()
            if not text:
                continue

            seat_block = detect_seat_block(text)

            # Strict college detection (start of line only)
            college_match = re.search(r"\n(\d{4,5})\s*-\s*(.+)", "\n" + text)
            if not college_match:
                continue

            college_code = college_match.group(1)
            college_name = college_match.group(2).strip()

            # Branch blocks
            branch_matches = re.findall(r"(\d{9,10})\s*-\s*(.+)", text)

            tables = page.extract_tables()
            if not tables or not branch_matches:
                continue

            for i, (branch_code, branch_name) in enumerate(branch_matches):

                if i >= len(tables):
                    break

                table = tables[i]
                if not table or len(table) < 2:
                    continue

                headers = []
                for h in table[0]:
                    if h:
                        headers.append(str(h).strip().replace("\n", ""))
                    else:
                        headers.append(None)

                for row in table[1:]:

                    for idx, cell in enumerate(row):
                        if idx >= len(headers):
                            continue

                        category = headers[idx]
                        if not category:
                            continue

                        if not cell:
                            continue

                        match = rank_pattern.search(str(cell))
                        if not match:
                            continue

                        rows.append({
                            "year": year,
                            "round": round_num,
                            "examType": "MHTCET",
                            "quotaType": "STATE",
                            "seatAllocationType": seat_block,
                            "collegeCode": college_code,
                            "collegeName": college_name,
                            "branchCode": branch_code,
                            "branchName": branch_name.strip(),
                            "category": category,
                            "closingRank": int(match.group(1)),
                            "closingPercentile": float(match.group(2))
                        })


# =====================================================
# =================== AI PDFs =========================
# =====================================================
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

            text = page.extract_text()
            if not text:
                continue

            # Collapse line breaks between wrapped institute names
            text = re.sub(r"\n(?=\s)", " ", text)

            # Match core numeric structure instead of rigid text phrases
            pattern = re.compile(
                r"(\d{4,5})\s*-\s*(.*?)\s+"
                r"\d+\s+"
                r"(\d+)\s*\(([\d.]+)\)\s+"
                r"(\d{9,10}[A-Z]?)\s+AI\s+AI\s+"
                r"(?:JEE.*?|MHT-CET.*?|NEET.*?)\s+to\s+AI\s+(.+?)(?=\s+\d{4,5}\s*-|\Z)",
                re.DOTALL
            )

            matches = pattern.findall(text)

            for m in matches:
                rows.append({
                    "year": year,
                    "round": round_num,
                    "examType": "JEE",  # All India block
                    "quotaType": "ALL_INDIA",
                    "seatAllocationType": "ALL_INDIA",
                    "collegeCode": m[0],
                    "collegeName": m[1].strip(),
                    "branchCode": m[4],
                    "branchName": m[5].replace("\n", " ").strip(),
                    "category": "AI",
                    "closingRank": int(m[2]),
                    "closingPercentile": float(m[3])
                })
# =====================================================
# =================== SAVE ============================
# =====================================================
df = pd.DataFrame(rows)

print("\nTotal Rows:", len(df))
print("\nRows Per Year:")
print(df.groupby("year").size())

print("\nExamType Distribution:")
print(df["examType"].value_counts())

Path("output").mkdir(exist_ok=True)

if Path(OUTPUT_FILE).exists():
    Path(OUTPUT_FILE).unlink()

wb = Workbook()
ws = wb.active
ws.title = "MasterCutoffData"

for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

wb.save(OUTPUT_FILE)

print("✅ MASTER DATA GENERATED:", OUTPUT_FILE) 