import io
import os
import re
import streamlit as st
import duckdb
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARQUET_FILE = os.path.join(SCRIPT_DIR, "bps_data.parquet").replace(os.sep, "/")

st.set_page_config(
    page_title="BPS Statistical Multi-Table Selector & Exporter",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS & Font Injection based on update.py Glassmorphism & Typewriter Style
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Courier Prime', 'Space Mono', Courier, monospace !important;
    letter-spacing: -0.01em;
}

/* Background Soft Gradient */
.stApp {
    background: 
        radial-gradient(circle at 10% 20%, rgba(186, 230, 253, 0.9) 0%, rgba(224, 231, 255, 0.7) 35%, transparent 70%),
        radial-gradient(circle at 85% 25%, rgba(243, 232, 255, 0.95) 0%, rgba(219, 234, 254, 0.6) 45%, transparent 70%),
        radial-gradient(circle at 50% 80%, rgba(233, 213, 255, 0.8) 0%, rgba(199, 210, 254, 0.7) 40%, transparent 75%),
        linear-gradient(135deg, #e0f2fe 0%, #ede9fe 50%, #fdf4ff 100%) !important;
    background-attachment: fixed !important;
    color: #1e293b !important;
}

/* Glass Cards */
.glass-header-card {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.45);
    border-top: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 24px;
    box-shadow: 0 10px 32px 0 rgba(31, 38, 135, 0.08), inset 0 1px 1px 0 rgba(255, 255, 255, 0.5);
}

.glass-section-card {
    background: rgba(255, 255, 255, 0.10);
    backdrop-filter: blur(20px) saturate(150%);
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-top: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px 0 rgba(31, 38, 135, 0.06), inset 0 1px 1px 0 rgba(255, 255, 255, 0.4);
}

.glass-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.5);
    color: #334155;
    margin-bottom: 10px;
}

/* Streamlit Input & Multi-select Glass Styling */
div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.14) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.6) !important;
    border-radius: 14px !important;
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.3) !important;
    color: #0f172a !important;
}

div[data-baseweb="select"] > div:hover {
    background: rgba(255, 255, 255, 0.22) !important;
    border-color: rgba(165, 180, 252, 0.7) !important;
}

/* Tags in multi-select */
span[data-baseweb="tag"] {
    background: rgba(255, 255, 255, 0.30) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    border-radius: 9999px !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: rgba(255, 255, 255, 0.20) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 16px !important;
    color: #0f172a !important;
    font-family: 'Courier Prime', 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 12px 28px !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.12), inset 0 1px 2px rgba(255, 255, 255, 0.6) !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.stButton > button:hover {
    background: rgba(255, 255, 255, 0.35) !important;
    border-color: rgba(255, 255, 255, 0.8) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(99, 102, 241, 0.18), inset 0 1px 2px rgba(255, 255, 255, 0.8) !important;
}

.stDownloadButton > button {
    background: rgba(167, 243, 208, 0.30) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(110, 231, 183, 0.55) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 16px !important;
    color: #064e3b !important;
    font-family: 'Courier Prime', 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 12px 28px !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.15) !important;
    transition: all 0.25s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(167, 243, 208, 0.45) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(16, 185, 129, 0.22) !important;
}

/* Dataframe Container */
[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    border-radius: 16px !important;
    padding: 10px !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="glass-header-card">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <div class="glass-badge">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#0284c7;"></span>
                BPS Statistical System
            </div>
            <h1 style="font-size: 24px; font-weight: 800; margin: 0 0 8px 0; color: #0f172a;">
                BPS Statistical Multi-Table Selector &amp; Exporter
            </h1>
            <p style="font-size: 13px; color: #475569; margin: 0; max-width: 650px; line-height: 1.5;">
                Saring data statistik wilayah bertingkat, pratinjau tabel pivot 2D, dan ekspor ke lembar kerja Excel gabungan.
            </p>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 10px 18px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.4); text-align: right;">
            <div style="font-size: 11px; color: #64748b; font-weight: 500;">Database Engine</div>
            <div style="font-size: 13px; color: #0f172a; font-weight: 700;">DuckDB Parquet</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(PARQUET_FILE):
    st.error(f"File database belum ditemukan: {PARQUET_FILE}. Silakan jalankan 'python selector/build_parquet.py' terlebih dahulu.")
    st.stop()

@st.cache_resource
def get_db():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW IF NOT EXISTS data AS SELECT * FROM read_parquet('{PARQUET_FILE}')")
    return con

con = get_db()

# Filter Columns Layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="glass-section-card">
        <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 8px;">
            Filter Wilayah Administrasi (Hirarki Bertingkat)
        </div>
    </div>
    """, unsafe_allow_html=True)

    prov_all = [r[0] for r in con.execute("SELECT DISTINCT Provinsi FROM data WHERE Provinsi IS NOT NULL ORDER BY Provinsi").fetchall()]
    sel_prov = st.multiselect("1. Pilih Provinsi (bisa pilih banyak)", prov_all)

    kab_query = "SELECT DISTINCT Kabupaten FROM data WHERE Kabupaten IS NOT NULL"
    params_kab = []
    if sel_prov:
        kab_query += f" AND Provinsi IN ({','.join(['?']*len(sel_prov))})"
        params_kab.extend(sel_prov)
    kab_all = [r[0] for r in con.execute(kab_query + " ORDER BY Kabupaten", params_kab).fetchall()]
    sel_kab = st.multiselect("2. Pilih Kabupaten/Kota (bisa pilih banyak)", kab_all)

    kec_query = "SELECT DISTINCT Kecamatan FROM data WHERE Kecamatan IS NOT NULL"
    params_kec = []
    if sel_prov:
        kec_query += f" AND Provinsi IN ({','.join(['?']*len(sel_prov))})"
        params_kec.extend(sel_prov)
    if sel_kab:
        kec_query += f" AND Kabupaten IN ({','.join(['?']*len(sel_kab))})"
        params_kec.extend(sel_kab)
    kec_all = [r[0] for r in con.execute(kec_query + " ORDER BY Kecamatan", params_kec).fetchall()]
    sel_kec = st.multiselect("3. Pilih Kecamatan (bisa pilih banyak)", kec_all)

with col2:
    st.markdown("""
    <div class="glass-section-card">
        <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 8px;">
            Filter Periode &amp; Judul Tabel (Parameter Data)
        </div>
    </div>
    """, unsafe_allow_html=True)

    thn_query = "SELECT DISTINCT Tahun FROM data WHERE Tahun IS NOT NULL"
    params_thn = []
    if sel_prov:
        thn_query += f" AND Provinsi IN ({','.join(['?']*len(sel_prov))})"
        params_thn.extend(sel_prov)
    if sel_kab:
        thn_query += f" AND Kabupaten IN ({','.join(['?']*len(sel_kab))})"
        params_thn.extend(sel_kab)
    if sel_kec:
        thn_query += f" AND Kecamatan IN ({','.join(['?']*len(sel_kec))})"
        params_thn.extend(sel_kec)
    thn_all = [str(r[0]) for r in con.execute(thn_query + " ORDER BY Tahun", params_thn).fetchall()]
    sel_tahun = st.multiselect("4. Pilih Tahun (bisa pilih banyak)", thn_all)

    tbl_query = "SELECT DISTINCT Judul_Tabel FROM data WHERE Judul_Tabel IS NOT NULL"
    params_tbl = []
    if sel_prov:
        tbl_query += f" AND Provinsi IN ({','.join(['?']*len(sel_prov))})"
        params_tbl.extend(sel_prov)
    if sel_kab:
        tbl_query += f" AND Kabupaten IN ({','.join(['?']*len(sel_kab))})"
        params_tbl.extend(sel_kab)
    if sel_kec:
        tbl_query += f" AND Kecamatan IN ({','.join(['?']*len(sel_kec))})"
        params_tbl.extend(sel_kec)
    if sel_tahun:
        tbl_query += f" AND Tahun IN ({','.join(['?']*len(sel_tahun))})"
        params_tbl.extend(sel_tahun)
    
    tbl_all = [r[0] for r in con.execute(tbl_query + " ORDER BY Judul_Tabel", params_tbl).fetchall()]
    sel_tabel = st.multiselect("5. Pilih Tabel (opsional, kosongkan untuk pilih semua)", tbl_all)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Trigger Action Button
col_btn_center = st.columns([1, 2, 1])
with col_btn_center[1]:
    execute_btn = st.button("Tampilkan & Siapkan File Excel", use_container_width=True)

if execute_btn:
    with st.spinner("Mengambil dan menyusun tabel-tabel 2D..."):
        base_query = """
            SELECT Provinsi, Kabupaten, Kecamatan, Tahun, Sektor, Nomor_Tabel, Judul_Tabel,
                   Uraian_Indikator, Variabel_Kolom, Nilai_Statistik
            FROM data
            WHERE 1=1
        """
        params = []
        if sel_prov:
            base_query += f" AND Provinsi IN ({','.join(['?']*len(sel_prov))})"
            params.extend(sel_prov)
        if sel_kab:
            base_query += f" AND Kabupaten IN ({','.join(['?']*len(sel_kab))})"
            params.extend(sel_kab)
        if sel_kec:
            base_query += f" AND Kecamatan IN ({','.join(['?']*len(sel_kec))})"
            params.extend(sel_kec)
        if sel_tahun:
            base_query += f" AND Tahun IN ({','.join(['?']*len(sel_tahun))})"
            params.extend(sel_tahun)
        if sel_tabel:
            base_query += f" AND Judul_Tabel IN ({','.join(['?']*len(sel_tabel))})"
            params.extend(sel_tabel)

        raw_df = con.execute(base_query, params).df()

    if raw_df.empty:
        st.warning("Tidak ada data yang ditemukan dengan kriteria filter tersebut.")
    else:
        table_groups = raw_df.groupby(["Provinsi", "Kabupaten", "Kecamatan", "Tahun", "Nomor_Tabel", "Judul_Tabel"], sort=False)
        total_tables = len(table_groups)

        st.markdown(f"""
        <div class="glass-section-card" style="border-color: rgba(16, 185, 129, 0.4); display: flex; justify-content: space-between; align-items: center;">
            <div style="font-weight: 700; color: #064e3b; font-size: 13px;">
                Ditemukan <strong>{total_tables} tabel unik</strong> dari kombinasi filter yang dipilih.
            </div>
            <span style="background: rgba(16, 185, 129, 0.15); color: #065f46; font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 9999px;">
                Siap Ekspor
            </span>
        </div>
        """, unsafe_allow_html=True)

        wb = openpyxl.Workbook()
        ws_catalog = wb.active
        ws_catalog.title = "Daftar_Tabel"

        font_banner = Font(name="Segoe UI", size=11, bold=True, color="1F4E78")
        font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        font_data = Font(name="Segoe UI", size=10)
        border_thin = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        ws_catalog.append(["No", "Provinsi", "Kabupaten", "Kecamatan", "Tahun", "Nomor Tabel", "Judul Tabel", "Nama Sheet"])
        for col_i in range(1, 9):
            c = ws_catalog.cell(row=1, column=col_i)
            c.font = font_header
            c.fill = fill_header

        preview_count = 0
        cat_no = 1

        for (prov, kab, kec, thn, no_t, title), group in table_groups:
            pivoted = group.pivot_table(
                index="Uraian_Indikator",
                columns="Variabel_Kolom",
                values="Nilai_Statistik",
                aggfunc="first"
            ).reset_index()
            pivoted.rename(columns={"Uraian_Indikator": "Uraian / Wilayah"}, inplace=True)
            pivoted.fillna("-", inplace=True)

            clean_sheet_name = re.sub(r'[\\/*?:"<>|]', '_', f"{kec}_{thn}")[:31]
            if clean_sheet_name not in wb.sheetnames:
                ws = wb.create_sheet(title=clean_sheet_name)
            else:
                ws = wb[clean_sheet_name]

            ws_catalog.append([cat_no, prov, kab, kec, thn, no_t or "-", title, clean_sheet_name])
            cat_no += 1

            t_banner = f"[{kec} - {thn}] {('Tabel ' + str(no_t) + ': ') if no_t and no_t != '-' else ''}{title}"
            ws.append([t_banner])
            ws.cell(row=ws.max_row, column=1).font = font_banner

            headers = list(pivoted.columns)
            ws.append(headers)
            h_row = ws.max_row
            for col_i in range(1, len(headers) + 1):
                c = ws.cell(row=h_row, column=col_i)
                c.font = font_header
                c.fill = fill_header
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = border_thin

            for _, r in pivoted.iterrows():
                row_vals = [r[col] for col in headers]
                ws.append(row_vals)
                d_row = ws.max_row
                for col_i in range(1, len(headers) + 1):
                    c = ws.cell(row=d_row, column=col_i)
                    c.font = font_data
                    c.border = border_thin

            ws.append([])
            ws.append([])

            if preview_count < 5:
                with st.expander(f"Preview {preview_count + 1} dari {total_tables}: {t_banner}", expanded=(preview_count == 0)):
                    st.dataframe(pivoted, use_container_width=True)
                preview_count += 1

        if total_tables > 5:
            st.caption(f"...dan {total_tables - 5} tabel lainnya telah disusun ke dalam file Excel.")

        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col[:60]:
                    if cell.value:
                        lines = str(cell.value).split('\n')
                        max_len = max(max_len, len(lines[0]))
                sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label=f"Download Seluruh Tabel Terpilih ({total_tables} Tabel dalam 1 File .xlsx)",
            data=output,
            file_name="bps_multi_tables_exported.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
