import sys
sys.path.append('.')
from extract_worker import clean_cell, merge_multi_level_headers

row0 = ['B u l a n', 'Curah Hujan (mm)', None, None, 'Hari Hujan (HH)', None, None]
row1 = [None, '2016', '2017', '2018', '2016', 'd2017\ni', '2018']

print("Row 0 cleaned:", [clean_cell(c) for c in row0])
print("Row 1 cleaned:", [clean_cell(c) for c in row1])

res = merge_multi_level_headers([row0, row1])
print("Merged headers:", res)

