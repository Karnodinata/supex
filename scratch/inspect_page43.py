import pdfplumber

with pdfplumber.open("sample_test.pdf") as pdf:
    p = pdf.pages[42] # Page 43 (0-indexed 42)
    print("Page 43 text:\n", p.extract_text())
    print("\nCurves count:", len(p.curves))
    print("Lines count:", len(p.lines))
    print("Rects count:", len(p.rects))
    
    # Try with different table_settings
    print("\nDefault extract_tables:", len(p.extract_tables()))
    
    # Try text-based table extraction (stream mode)
    stream_tables = p.extract_tables({
        "vertical_strategy": "text",
        "horizontal_strategy": "text"
    })
    print("Stream extract_tables (text-based):", len(stream_tables))
    if stream_tables:
        print(f"Stream table: {len(stream_tables[0])} rows x {len(stream_tables[0][0])} cols")
        for r in stream_tables[0][:6]:
            print("  ", [c.replace('\n', ' ') if c else '' for c in r])

