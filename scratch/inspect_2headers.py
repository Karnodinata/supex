import pdfplumber
import json

with pdfplumber.open("sample_test.pdf") as pdf:
    for idx, page in enumerate(pdf.pages):
        raw_tables = page.extract_tables()
        if not raw_tables:
            continue
        for t_idx, raw_tbl in enumerate(raw_tables):
            if len(raw_tbl) > 3:
                # Check first 3 rows
                r0 = [c.replace('\n', ' ') if c else '' for c in raw_tbl[0]]
                r1 = [c.replace('\n', ' ') if c else '' for c in raw_tbl[1]]
                r2 = [c.replace('\n', ' ') if c else '' for c in raw_tbl[2]]
                
                # Check if r0 or r1 have merged/empty cells indicating multi-level header
                empty_in_r0 = sum(1 for c in r0 if not c)
                empty_in_r1 = sum(1 for c in r1 if not c)
                if empty_in_r0 > 0 or empty_in_r1 > 0:
                    print(f"\n--- Page {idx+1} Table {t_idx+1} ({len(raw_tbl)} rows x {len(r0)} cols) ---")
                    print("Row 0:", r0)
                    print("Row 1:", r1)
                    print("Row 2:", r2)

