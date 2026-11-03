import sys
sys.path.append('.')
import pdfplumber
from extract_worker import clean_cell, is_guide_row, merge_multi_level_headers, extract_raw_page_table

def test_page(p_num):
    with pdfplumber.open("sample_test.pdf") as pdf:
        p = pdf.pages[p_num - 1]
        raw_tbl = extract_raw_page_table(p)
        cleaned_grid = []
        for row in raw_tbl:
            cleaned_row = [clean_cell(c) for c in row]
            if any(cleaned_row):
                cleaned_grid.append(cleaned_row)
        
        guide_idx = -1
        for g_i in range(min(5, len(cleaned_grid))):
            if is_guide_row(cleaned_grid[g_i]):
                guide_idx = g_i
                break
                
        candidate_headers = []
        if guide_idx != -1:
            for h_i in range(guide_idx):
                row_h = cleaned_grid[h_i]
                row_str = ' '.join(row_h).strip()
                # Skip document banners
                if any(kw in row_str.lower() for kw in ['dalam angka', 'katalog bps', 'nomor publikasi', 'tabel statistik']):
                    continue
                if not any(row_h):
                    continue
                candidate_headers.append(row_h)
        else:
            candidate_headers = [cleaned_grid[0]]
            
        merged = merge_multi_level_headers(candidate_headers)
        print(f"\n[Page {p_num}] Headers ({len(merged)} cols):")
        for idx, h in enumerate(merged):
            print(f"  Col {idx}: {h}")

test_page(26)
test_page(43)
test_page(61)

