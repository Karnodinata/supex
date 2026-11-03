import sys
sys.path.append('.')
import pdfplumber
from extract_worker import clean_cell, is_guide_row, extract_raw_page_table, parse_single_or_merged_table

with pdfplumber.open("sample_test.pdf") as pdf:
    # Test Page 26
    p26 = pdf.pages[25]
    raw26 = extract_raw_page_table(p26)
    print("Page 26 raw rows 0, 1, 2:")
    for r in raw26[:4]:
        print("  Raw:", r)
        print("  Cleaned:", [clean_cell(c) for c in r])
        print("  is_guide_row:", is_guide_row(r))

    print("\n--- Page 43 ---")
    p43 = pdf.pages[42]
    raw43 = extract_raw_page_table(p43)
    print("Page 43 extract_raw_page_table returned:", len(raw43) if raw43 else 0)
    if raw43:
        for r in raw43[:6]:
            print("  Raw:", r)
            print("  Cleaned:", [clean_cell(c) for c in r])
            print("  is_guide_row:", is_guide_row(r))
            
    res43 = parse_single_or_merged_table(pdf, [43])
    print("parse_single_or_merged_table([43]) returned:", res43 is not None)
    if res43:
        print("Headers:", res43["headers"])
        print("Rows count:", res43["totalRows"])
