import pdfplumber
import re

def test_strategies(page_idx):
    with pdfplumber.open("sample_test.pdf") as pdf:
        p = pdf.pages[page_idx]
        print(f"\n=== PAGE {page_idx+1} ===")
        # Strategy 1: Default lines
        t1 = p.extract_tables()
        print(f"Default strategy: {len(t1)} tables")
        
        # Strategy 2: text strategy
        t2 = p.extract_tables({
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_y_tolerance": 4,
            "intersection_y_tolerance": 4
        })
        print(f"Text strategy: {len(t2)} tables")
        if t2:
            print("Text strategy sample rows:")
            for r in t2[0][:8]:
                clean_r = [c.replace('\n', ' ') if c else '' for c in r if c]
                if clean_r:
                    print("  ", clean_r)

for p_num in [43, 80, 81, 82]:
    test_strategies(p_num - 1)

