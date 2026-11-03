import sys
import json
import re
import os
import pdfplumber

def despace_common_words(text):
    patterns = [
        (r'\bB\s+u\s+l\s+a\s+n\b', 'Bulan'),
        (r'\bT\s+a\s+h\s+u\s+n\b', 'Tahun'),
        (r'\bJ\s+u\s+m\s+l\s+a\s+h\b', 'Jumlah'),
        (r'\bT\s+o\s+t\s+a\s+l\b', 'Total'),
        (r'\bN\s+a\s+m\s+a\b', 'Nama'),
        (r'\bD\s+e\s+s\s+a\b', 'Desa')
    ]
    res = text
    for pat, rep in patterns:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    return res

def clean_cell(raw_val):
    if raw_val is None:
        return ""
    s = str(raw_val).strip()
    if not s:
        return ""
        
    s = despace_common_words(s)
    
    # Ganti simbol centang
    s = s.replace('\u221a', 'Ya').replace('✓', 'Ya').replace('✔', 'Ya')
    
    # Filter pecahan watermark vertikal
    lines = s.split('\n')
    cleaned_lines = []
    for l in lines:
        l_str = l.strip()
        if len(l_str) == 1 and not l_str.isdigit():
            continue
        # Watermark tokens bps.go.id / acehbaratkab
        if re.match(r'^(?:[diogspbakthrce/\.:]\s*)+$', l_str, re.IGNORECASE) and len(l_str) <= 6:
            continue
        cleaned_lines.append(l_str)
    s = ' '.join(cleaned_lines)
    
    # Hapus huruf tercecer watermark di awal/akhir
    s = re.sub(r'^(?:[diogspbakthrce\.\:\/]\s+)+', '', s)
    s = re.sub(r'(?:\s+[diogspbakthrce\.\:\/])+$', '', s)
    s = re.sub(r'\s+[diogspbakthrce]\s+', ' ', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*[\/]{2,}\s*', ' / ', s)
    s = re.sub(r'\s*\:\s*$', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    
    # Rapikan watermark pada angka
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
        
    if s.lower() == 'mpok umur':
        return 'Kelompok Umur'
        
    return s

def is_guide_row(row):
    cleaned = [clean_cell(c) for c in row if c and str(c).strip()]
    if not cleaned:
        return False
    # Format (1), (2), (3)
    paren_matches = sum(1 for c in cleaned if re.match(r'^\s*\(?\s*\d{1,2}\s*\)?\.?\s*$', c) and '(' in c)
    if paren_matches >= max(1, len(cleaned) * 0.5):
        return True
    # Format angka kecil berurutan <= 25 (bukan tahun/data)
    small_ints = sum(1 for c in cleaned if c.isdigit() and 1 <= int(c) <= 25)
    return small_ints >= max(2, len(cleaned) * 0.8)

def merge_multi_level_headers(header_rows):
    if not header_rows:
        return []
    num_cols = max(len(r) for r in header_rows)
    normalized = []
    for r in header_rows:
        row_copy = [clean_cell(c) for c in r]
        while len(row_copy) < num_cols:
            row_copy.append("")
        normalized.append(row_copy)
        
    # Forward-propagate parent headers across merged empty columns
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
        
    # Gabungkan hirarki per kolom
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

def extract_raw_page_table(page):
    # Strategy 1: Lines-based
    raw_tables = page.extract_tables()
    if raw_tables and len(raw_tables[0]) >= 2:
        return raw_tables[0]
        
    # Strategy 2: Text-based fallback (untuk tabel tanpa garis/borderless)
    raw_tables_text = page.extract_tables({
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_y_tolerance": 5
    })
    if raw_tables_text and len(raw_tables_text[0]) >= 2:
        return raw_tables_text[0]
        
    return []

def parse_single_or_merged_table(pdf, page_numbers):
    if not page_numbers:
        return None
        
    master_headers = []
    master_rows = []
    
    for idx, p_num in enumerate(page_numbers):
        if p_num < 1 or p_num > len(pdf.pages):
            continue
        page = pdf.pages[p_num - 1]
        raw_tbl = extract_raw_page_table(page)
        if not raw_tbl:
            continue
            
        cleaned_grid = []
        for row in raw_tbl:
            cleaned_row = [clean_cell(c) for c in row]
            if any(cleaned_row):
                cleaned_grid.append(cleaned_row)
                
        if not cleaned_grid or len(cleaned_grid) < 2:
            continue
            
        # Cari letak baris petunjuk / guide row: (1) (2) (3)...
        guide_idx = -1
        for g_i in range(min(5, len(cleaned_grid))):
            if is_guide_row(cleaned_grid[g_i]):
                guide_idx = g_i
                break
                
        if idx == 0:
            # Halaman Pertama: Tentukan Header
            if guide_idx != -1:
                data_start_idx = guide_idx + 1
                candidate_headers = []
                for h_i in range(guide_idx):
                    row_h = cleaned_grid[h_i]
                    row_str = ' '.join(row_h).strip()
                    # Lewati baris yang merupakan judul publikasi atau subtitle wilayah
                    if any(kw in row_str.lower() for kw in ['dalam angka', 'katalog bps', 'nomor publikasi', 'tabel statistik', 'dalam kecama', 'dalam kabupa']):
                        continue
                    if not any(row_h):
                        continue
                    candidate_headers.append(row_h)
                    
                if not candidate_headers and guide_idx > 0:
                    candidate_headers = [cleaned_grid[guide_idx - 1]]
                elif not candidate_headers:
                    candidate_headers = [cleaned_grid[0]]
                    
                master_headers = merge_multi_level_headers(candidate_headers)
            else:
                data_start_idx = 1
                if len(cleaned_grid) > 1 and not cleaned_grid[1][0] and any(cleaned_grid[1][1:]):
                    candidate_headers = [cleaned_grid[0], cleaned_grid[1]]
                    data_start_idx = 2
                else:
                    candidate_headers = [cleaned_grid[0]]
                master_headers = merge_multi_level_headers(candidate_headers)
                
            # Ambil data rows halaman pertama
            last_col0 = ""
            for r in cleaned_grid[data_start_idx:]:
                if is_guide_row(r) or not any(r):
                    continue
                if len(r) > 0 and re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', str(r[0])):
                    continue
                if len(r) > 0:
                    if r[0]:
                        last_col0 = r[0]
                    elif last_col0 and any(r[1:]):
                        r[0] = last_col0
                while len(r) < len(master_headers):
                    r.append("")
                master_rows.append(r[:len(master_headers)])
                
        else:
            # Halaman Lanjutan (Continued table):
            # Lewati pengulangan header dan guide row
            if guide_idx != -1:
                data_start_idx = guide_idx + 1
            else:
                data_start_idx = 1
                if len(cleaned_grid) > 1 and not cleaned_grid[1][0] and any(cleaned_grid[1][1:]):
                    data_start_idx = 2
                    
            last_col0 = ""
            for r in cleaned_grid[data_start_idx:]:
                if is_guide_row(r) or not any(r):
                    continue
                if len(r) > 0 and re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', str(r[0])):
                    continue
                if len(r) > 0:
                    if r[0]:
                        last_col0 = r[0]
                    elif last_col0 and any(r[1:]):
                        r[0] = last_col0
                while len(r) < len(master_headers):
                    r.append("")
                master_rows.append(r[:len(master_headers)])
                
    if master_headers and master_rows:
        return {
            "headers": master_headers,
            "rows": master_rows,
            "totalRows": len(master_rows),
            "totalCols": len(master_headers),
            "pagesIncluded": page_numbers
        }
    return None

def process_request(pdf_path, table_specs):
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        if isinstance(table_specs, dict):
            for t_id, pages in table_specs.items():
                p_list = [int(p) for p in pages if str(p).isdigit()]
                tbl_res = parse_single_or_merged_table(pdf, p_list)
                if tbl_res:
                    results[t_id] = tbl_res
        elif isinstance(table_specs, list):
            for item in table_specs:
                if isinstance(item, dict) and "pages" in item:
                    t_id = item.get("id", str(item["pages"][0]))
                    p_list = [int(p) for p in item["pages"] if str(p).isdigit()]
                    tbl_res = parse_single_or_merged_table(pdf, p_list)
                    if tbl_res:
                        results[t_id] = tbl_res
                elif str(item).isdigit():
                    p = int(item)
                    tbl_res = parse_single_or_merged_table(pdf, [p])
                    if tbl_res:
                        results[str(p)] = tbl_res
    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Usage: extract_worker.py <pdf_path> <specs_json_or_csv>"}))
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    raw_spec = sys.argv[2]
    
    try:
        if raw_spec.startswith("{") or raw_spec.startswith("["):
            specs = json.loads(raw_spec)
        else:
            specs = [int(p.strip()) for p in raw_spec.split(",") if p.strip().isdigit()]
            
        data = process_request(pdf_path, specs)
        print(json.dumps({"success": True, "results": data}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
