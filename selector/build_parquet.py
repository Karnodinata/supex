import os
import glob
import pandas as pd
import duckdb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
EXCEL_DIR = os.path.join(BASE_DIR, "output_kabupaten")
PARQUET_FILE = os.path.join(SCRIPT_DIR, "bps_data.parquet")

excel_files = glob.glob(os.path.join(EXCEL_DIR, "*.xlsx"))
print(f"Total file Excel ditemukan: {len(excel_files)}")

if not excel_files:
    print(f"Tidak ada file Excel ditemukan di: {EXCEL_DIR}")
    exit(1)

dfs = []
for i, f in enumerate(excel_files, 1):
    try:
        df = pd.read_excel(f, sheet_name="Data_Visualisasi")
        if not df.empty:
            dfs.append(df)
        if i % 20 == 0 or i == len(excel_files):
            print(f"[{i}/{len(excel_files)}] file terbaca...")
    except Exception as e:
        print(f"Skip {os.path.basename(f)}: {e}")

if not dfs:
    print("Tidak ada data yang berhasil diekstrak.")
    exit(1)

master_df = pd.concat(dfs, ignore_index=True)

con = duckdb.connect()
con.register("df_view", master_df)
con.execute(f"COPY df_view TO '{PARQUET_FILE.replace(os.sep, '/')}' (FORMAT PARQUET, COMPRESSION ZSTD)")

size_mb = os.path.getsize(PARQUET_FILE) / (1024 * 1024)
print(f"Selesai. File tersimpan di: {PARQUET_FILE} ({size_mb:.2f} MB)")
