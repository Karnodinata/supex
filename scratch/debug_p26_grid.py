import sys
sys.path.append('.')
import pdfplumber
from extract_worker import clean_cell, is_guide_row, extract_raw_page_table

with pdfplumber.open("sample_test.pdf") as pdf:
    p = pdf.pages[25] # Page 26
    raw_tbl = extract_raw_page_table(p)
    cleaned_grid = []
    for row in raw_tbl:
        cleaned_row = [clean_cell(c) for c in row]
        if any(cleaned_row):
            cleaned_grid.append(cleaned_row)
    
    print("Cleaned grid len:", len(cleaned_grid))
    for i in range(min(6, len(cleaned_grid))):
        print(f"Row {i} (guide={is_guide_row(cleaned_grid[i])}):", cleaned_grid[i])

