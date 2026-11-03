import pdfplumber
import re

def clean_cell(raw_val):
    if raw_val is None:
        return ""
    s = str(raw_val).strip()
    if not s:
        return ""
    s = s.replace('\u221a', 'Ya').replace('✓', 'Ya').replace('✔', 'Ya')
    lines = s.split('\n')
    cleaned_lines = []
    for l in lines:
        l_str = l.strip()
        if len(l_str) == 1 and not l_str.isdigit():
            continue
        if re.match(r'^(?:[diogspbakthrce/\.:]\s*)+$', l_str, re.IGNORECASE) and len(l_str) <= 6:
            continue
        cleaned_lines.append(l_str)
    s = ' '.join(cleaned_lines)
    s = re.sub(r'^(?:[a-zA-Z\.\:\/]\s+)+', '', s)
    s = re.sub(r'(?:\s+[a-zA-Z\.\:\/])+$', '', s)
    s = re.sub(r'\s+[diogspbakthrce]\s+', ' ', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*[\/]{2,}\s*', ' / ', s)
    s = re.sub(r'\s*\:\s*$', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if re.search(r'\d', s):
        stripped_num = re.sub(r'[diogspbakthrce/\.:\s]', '', s)
        if re.match(r'^-?\d+(?:[\.,]\d+)?$', stripped_num):
            if ',' in s or '.' in s:
                m = re.search(r'\d+[\.,]\d+', s)
                if m:
                    return m.group(0)
            return stripped_num
    if re.match(r'^(?:[diogspbakthrce/\.:\s])+$', s, re.IGNORECASE):
        return ""
    return s

def is_guide_row(row):
    non_empty = [c for c in row if c and c.strip()]
    if not non_empty:
        return True
    return all(re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', c) for c in non_empty)

def merge_multi_level_headers(header_rows):
    num_cols = max(len(r) for r in header_rows)
    normalized = []
    for r in header_rows:
        row_copy = [clean_cell(c) for c in r]
        while len(row_copy) < num_cols:
            row_copy.append("")
        normalized.append(row_copy)
        
    propagated = []
    for lvl_idx, r in enumerate(normalized):
        prop_row = []
        last_val = ""
        for col_idx in range(num_cols):
            val = r[col_idx]
            if val:
                last_val = val
                prop_row.append(val)
            else:
                has_lower_sub = any(normalized[sub_lvl][col_idx] for sub_lvl in range(lvl_idx + 1, len(normalized)))
                if has_lower_sub and last_val:
                    prop_row.append(last_val)
                else:
                    prop_row.append("")
        propagated.append(prop_row)
        
    final_headers = []
    for c_idx in range(num_cols):
        parts = []
        for lvl in propagated:
            part = lvl[c_idx]
            if part and part not in parts:
                parts.append(part)
        if parts:
            final_headers.append(" - ".join(parts))
        else:
            final_headers.append(f"Kolom_{c_idx + 1}")
    return final_headers

# Test on page 26, 35, 61, 62
with pdfplumber.open("sample_test.pdf") as pdf:
    for p_num in [26, 35, 61, 62, 63]:
        p = pdf.pages[p_num - 1]
        raw_tables = p.extract_tables()
        if not raw_tables:
            continue
        grid = raw_tables[0]
        # Check header rows
        header_rows = [grid[0]]
        data_start = 1
        if len(grid) > 1 and is_guide_row(grid[1]):
            data_start = 2
        elif len(grid) > 2 and is_guide_row(grid[2]):
            header_rows = [grid[0], grid[1]]
            data_start = 3
        elif len(grid) > 3 and is_guide_row(grid[3]):
            header_rows = [grid[0], grid[1], grid[2]]
            data_start = 4
        elif len(grid) > 1 and not grid[1][0] and any(grid[1][1:]):
            header_rows = [grid[0], grid[1]]
            data_start = 2
            
        merged = merge_multi_level_headers(header_rows)
        print(f"\n[Page {p_num}] Headers ({len(merged)} cols):")
        for idx, h in enumerate(merged):
            print(f"  Col {idx}: {h}")
        print(f"  First data row: {grid[data_start][:5]}")

