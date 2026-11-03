import pdfplumber

with pdfplumber.open("sample_test.pdf") as pdf:
    p = pdf.pages[42] # Page 43
    # Try with explicit vertical lines or snap
    t_text = p.extract_tables({
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_y_tolerance": 5
    })
    print("Tables found with text strategy:", len(t_text))
    if t_text:
        print(f"Table 0 shape: {len(t_text[0])} rows x {len(t_text[0][0])} cols")
        for idx, r in enumerate(t_text[0]):
            clean = [c.replace('\n', ' ').strip() for c in r if c and c.strip()]
            if clean:
                print(f"Row {idx:02d}:", clean)

