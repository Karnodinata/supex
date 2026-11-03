import pdfplumber

with pdfplumber.open("sample_test.pdf") as pdf:
    p = pdf.pages[79]
    t = p.extract_tables({
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_y_tolerance": 5
    })
    if t:
        for idx, r in enumerate(t[0][5:20]):
            clean = [c.replace('\n', ' ').strip() for c in r if c and c.strip()]
            if clean:
                print(f"Row {idx+5}:", clean)

