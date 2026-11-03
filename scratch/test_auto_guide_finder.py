import sys
sys.path.append('.')
import re
import pdfplumber

def is_guide_row(row):
    from extract_worker import clean_cell
    cleaned = [clean_cell(c) for c in row if c and str(c).strip()]
    if not cleaned:
        return False
    paren_matches = sum(1 for c in cleaned if re.match(r'^\s*\(?\s*\d{1,2}\s*\)?\.?\s*$', c) and '(' in c)
    if paren_matches >= max(1, len(cleaned) * 0.5):
        return True
    small_ints = sum(1 for c in cleaned if c.isdigit() and 1 <= int(c) <= 25)
    return small_ints >= max(2, len(cleaned) * 0.8)

with pdfplumber.open("sample_test.pdf") as pdf:
    for p_num in [26, 43, 61, 80]:
        p = pdf.pages[p_num - 1]
        raw_tables = p.extract_tables()
        if not raw_tables:
            raw_tables = p.extract_tables({
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "snap_y_tolerance": 5
            })
        print(f"\n=== Page {p_num} (raw rows: {len(raw_tables[0]) if raw_tables else 0}) ===")
        if raw_tables:
            for idx, r in enumerate(raw_tables[0][:6]):
                print(f"Row {idx} (is_guide={is_guide_row(r)}):", [c.replace('\n', ' ') if c else '' for c in r])

