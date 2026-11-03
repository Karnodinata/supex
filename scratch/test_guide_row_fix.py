import sys
sys.path.append('.')
import re

def is_guide_row_fixed(row):
    from extract_worker import clean_cell
    cleaned = [clean_cell(c) for c in row if c and str(c).strip()]
    if not cleaned:
        return False
    paren_matches = sum(1 for c in cleaned if re.match(r'^\s*\(?\s*\d{1,2}\s*\)?\.?\s*$', c) and '(' in c)
    if paren_matches >= max(1, len(cleaned) * 0.5):
        return True
    # Sequential small numbers <= 25 without data-like large values
    small_ints = sum(1 for c in cleaned if c.isdigit() and 1 <= int(c) <= 25)
    return small_ints >= max(2, len(cleaned) * 0.8)

# Test cases
row_years = ['', '2016', '2017', '2018', '2016', '2017', '2018']
row_guide = ['(1)', '(3)', '(4)', '(3)', '(6)', '(7)', '(5)']
row_data = ['0-4', '655', '706', '1361']

print("row_years is guide?", is_guide_row_fixed(row_years))
print("row_guide is guide?", is_guide_row_fixed(row_guide))
print("row_data is guide?", is_guide_row_fixed(row_data))

