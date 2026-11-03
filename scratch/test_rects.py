import pdfplumber

with pdfplumber.open("sample_test.pdf") as pdf:
    p = pdf.pages[42] # Page 43
    print("Rects strategy:")
    t_rects = p.extract_tables({
        "vertical_strategy": "rects",
        "horizontal_strategy": "rects"
    })
    print(f"Rects: {len(t_rects)} tables")
    if t_rects:
        for r in t_rects[0][:10]:
            print("  ", [c.replace('\n', ' ') if c else '' for c in r])

    print("\nText strategy with crop below title:")
    # Crop page to table area below "Tabel 3.5" title
    # bbox: (x0, top, x1, bottom)
    crop = p.crop((p.bbox[0], 120, p.bbox[2], p.bbox[3] - 60))
    t_crop = crop.extract_tables({
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_y_tolerance": 5,
        "intersection_x_tolerance": 15
    })
    print(f"Cropped text: {len(t_crop)} tables")
    if t_crop:
        for r in t_crop[0][:8]:
            print("  ", [c.replace('\n', ' ') if c else '' for c in r])

