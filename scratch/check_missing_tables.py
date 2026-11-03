import pdfplumber
import json

with pdfplumber.open("sample_test.pdf") as pdf:
    for idx, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        has_table_title = False
        t_label = ""
        for l in lines[:6]:
            if "Tabel" in l or "Table" in l:
                has_table_title = True
                t_label = l
                break
        
        if has_table_title:
            raw_tables = page.extract_tables()
            table_count = len(raw_tables) if raw_tables else 0
            if table_count == 0:
                print(f"[!] PAGE {idx+1} HAS TABLE TITLE '{t_label}' BUT extract_tables() returned 0 tables!")
            else:
                r_count = len(raw_tables[0]) if raw_tables[0] else 0
                c_count = len(raw_tables[0][0]) if raw_tables[0] and raw_tables[0][0] else 0
                if r_count < 2:
                    print(f"[!] PAGE {idx+1} HAS TABLE TITLE '{t_label}' BUT extracted table only has {r_count} rows!")

