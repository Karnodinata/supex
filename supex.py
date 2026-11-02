import io
import os
import sys
import re
import json
import glob
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pdfplumber
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Pastikan UTF-8 encoding untuk terminal Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:

# ==============================================================================
# 1. STRUKTUR DATA STATISTIK
# ==============================================================================
@dataclass
class StatTable:
    table_id: str
    table_number: str
    title: str
    sector: str
    page_number: int
    headers: List[str]
    rows: List[List[str]]
    unit: Optional[str] = None
    source: Optional[str] = None

@dataclass
class DocumentStatsResult:
    file_id: str
    filename: str
    provinsi: str
    kabupaten_kota: str
    kecamatan: str
    year: str
    total_pages: int
    tables: List[StatTable]


# ==============================================================================
# 2. STATE & PROGRESS TRACKER (PER-FILE REAL-TIME TRACKING)
# ==============================================================================
class ProgressTracker:
    def __init__(self, tracker_file: str = "progress_tracker.json"):
        self.tracker_file = tracker_file
        self.state = {
            "completed_files": {},      # file_id -> timestamp
            "completed_kabupatens": [], # list of kab keys
            "processed_files_count": 0,
            "last_updated": None,
            "failed_files": []
        }
        self.load()

    def load(self):
        # Muat status global dari progress_tracker.json dan seluruh progress_tracker_w*.json
        all_trackers = set()
        if os.path.exists("progress_tracker.json"):
            all_trackers.add("progress_tracker.json")
        for f in glob.glob("progress_tracker_w*.json"):
            all_trackers.add(f)
        if os.path.exists(self.tracker_file):
            all_trackers.add(self.tracker_file)

        for tf in all_trackers:
            try:
                with open(tf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    c_files = data.get("completed_files", {})
                    if isinstance(c_files, list):
                        c_files = {fid: True for fid in c_files}
                    for fid, ts in c_files.items():
                        self.state["completed_files"][fid] = ts
                    for kab in data.get("completed_kabupatens", []):
                        if kab not in self.state["completed_kabupatens"]:
                            self.state["completed_kabupatens"].append(kab)
            except Exception:
                pass
        self.state["processed_files_count"] = len(self.state["completed_files"])

    def save(self):
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tmp_file = f"{self.tracker_file}.tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.tracker_file)
        except Exception:
            try:
                with open(self.tracker_file, "w", encoding="utf-8") as f:
                    json.dump(self.state, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def is_file_completed(self, file_id: str) -> bool:
        return file_id in self.state.get("completed_files", {})

    def mark_file_completed(self, file_id: str, filename: str):
        self.state.setdefault("completed_files", {})[file_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state["processed_files_count"] = len(self.state["completed_files"])
        self.save()

    def is_kabupaten_completed(self, kab_key: str, output_path: str) -> bool:
        return (kab_key in self.state.get("completed_kabupatens", [])) and os.path.exists(output_path)

    def mark_kabupaten_completed(self, kab_key: str):
        if kab_key not in self.state.setdefault("completed_kabupatens", []):
            self.state["completed_kabupatens"].append(kab_key)
        self.save()

    def log_failure(self, file_info: Dict[str, Any], error_msg: str):
        self.state.setdefault("failed_files", []).append({
            "name": file_info.get("name", "Unknown"),
            "path": file_info.get("path", ""),
            "error": str(error_msg),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save()


# ==============================================================================
# 3. UNIVERSAL RECURSIVE STREAMER (CACHE-ENABLED)
# ==============================================================================
class UniversalStreamer:
    def __init__(self, source_path_or_url: str, cache_file: str = "gdrive_file_index.json"):
        self.source = source_path_or_url
        self.cache_file = cache_file
        self.is_gdrive = "drive.google.com" in source_path_or_url or (not os.path.exists(source_path_or_url) and len(source_path_or_url) > 20)

    def list_files(self, force_rescan: bool = False) -> List[Dict[str, Any]]:
        # 1. Cek Cache Lokal jika mode GDrive
        if self.is_gdrive and not force_rescan and os.path.exists(self.cache_file):
            try:
                print(f"[*] Memuat indeks file Google Drive dari cache lokal: '{self.cache_file}'...", flush=True)
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached:
                    print(f"[OK] Berhasil memuat {len(cached):,} file PDF dari cache lokal (Instan 0.1s).\n", flush=True)
                    return cached
            except Exception:
                pass

        file_list = []
        if not self.is_gdrive:
            # Mode Folder Lokal
            print(f"[*] Memindai folder lokal: '{self.source}'...", flush=True)
            for root, _, files in os.walk(self.source):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, self.source)
                        parts = rel_p.replace('/', '\\').split('\\')
                        prov = parts[0] if len(parts) > 2 else "Provinsi_Umum"
                        kab = parts[1] if len(parts) > 2 else (parts[0] if len(parts) == 2 else "Kabupaten_Umum")
                        file_list.append({
                            "id": f,
                            "name": f,
                            "path": full_p,
                            "rel_path": rel_p,
                            "provinsi": prov,
                            "kabupaten": kab,
                            "type": "local"
                        })
            print(f"[OK] Ditemukan {len(file_list)} file PDF di folder lokal.\n", flush=True)
            return file_list
        else:
            # Mode Google Drive Recursive
            import gdown
            print(f"[*] Memindai struktur folder Google Drive 34 Provinsi...", flush=True)
            raw_files = gdown.download_folder(self.source, skip_download=True, quiet=False)
            if raw_files:
                for f in raw_files:
                    f_path = getattr(f, 'path', '')
                    if f_path and f_path.lower().endswith('.pdf'):
                        parts = f_path.replace('/', '\\').split('\\')
                        prov = parts[0] if len(parts) >= 2 else "Provinsi_Umum"
                        kab = parts[1] if len(parts) >= 3 else (parts[0] if len(parts) == 2 else "Kabupaten_Umum")
                        file_list.append({
                            "id": f.id,
                            "name": os.path.basename(f_path),
                            "path": f_path,
                            "provinsi": prov,
                            "kabupaten": kab,
                            "type": "gdrive"
                        })
            print(f"\n[OK] Berhasil memetakan total {len(file_list):,} file PDF di Google Drive.", flush=True)
            
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(file_list, f, ensure_ascii=False)
                print(f"[OK] Indeks folder telah disimpan permanen ke '{self.cache_file}'.\n", flush=True)
            except Exception:
                pass

            return file_list

    def stream_to_memory(self, file_info: Dict[str, Any], max_retries: int = 3) -> io.BytesIO:
        if file_info.get("type") == "local":
            with open(file_info["path"], "rb") as f:
                return io.BytesIO(f.read())
        else:
            import requests
            url = "https://docs.google.com/uc?export=download"
            
            for attempt in range(1, max_retries + 1):
                try:
                    session = requests.Session()
                    response = session.get(url, params={'id': file_info["id"]}, stream=True, timeout=60)
                    for key, value in response.cookies.items():
                        if key.startswith('download_warning'):
                            response = session.get(url, params={'id': file_info["id"], 'confirm': value}, stream=True, timeout=60)
                            break
                    
                    memory_buffer = io.BytesIO()
                    for chunk in response.iter_content(chunk_size=1024 * 1024 * 2):
                        if chunk:
                            memory_buffer.write(chunk)
                    memory_buffer.seek(0)
                    return memory_buffer
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    time.sleep(2 * attempt)
            raise RuntimeError(f"Gagal stream file {file_info.get('name')}")


# ==============================================================================
# 4. BPS STATISTICAL TABLE PARSER & ADVANCED TEXT CLEANER
# ==============================================================================
class BPSStatisticalParser:
    SECTORS_MAP = {
        "1": "1_Geografi_Iklim",
        "2": "2_Pemerintahan",
        "3": "3_Penduduk",
        "4": "4_Sosial",
        "5": "5_Pertanian",
        "6": "6_Energi_Perdagangan",
        "7": "7_Transportasi_Lainnya"
    }

    @classmethod
    def clean_cell(cls, raw_val: Any) -> str:
        if raw_val is None:
            return ""
        s = str(raw_val).strip()
        if not s:
            return ""
        
        # 1. Simbol centang
        s = s.replace('\u221a', 'Ya').replace('✓', 'Ya').replace('✔', 'Ya')
        
        # 2. Filter baris pecahan watermark vertikal
        lines = s.split('\n')
        cleaned_lines = []
        for l in lines:
            l_str = l.strip()
            if len(l_str) == 1 and not l_str.isdigit():
                continue
            if re.match(r'^(?:[diogspbakthrce/\.:]\s*)+$', l_str, re.IGNORECASE) and len(l_str) <= 6:
                continue
            cleaned_lines.append(l_str)
        
        s = ' '.join(cleaned_lines)
        
        # 3. Bersihkan huruf watermark tunggal yang tercecer
        s = re.sub(r'^(?:[a-zA-Z\.\:\/]\s+)+', '', s)
        s = re.sub(r'(?:\s+[a-zA-Z\.\:\/])+$', '', s)
        s = re.sub(r'\s+[diogspbakthrce]\s+', ' ', s, flags=re.IGNORECASE)
        
        # 4. Rapikan tanda baca & spasi
        s = re.sub(r'\s*[\/]{2,}\s*', ' / ', s)
        s = re.sub(r'\s*\:\s*$', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        
        # 5. Bersihkan sel angka tertempel watermark
        if re.search(r'\d', s):
            stripped_num = re.sub(r'[diogspbakthrce/\.:\s]', '', s)
            if re.match(r'^-?\d+(?:[\.,]\d+)?$', stripped_num):
                if ',' in s or '.' in s:
                    m = re.search(r'\d+[\.,]\d+', s)
                    if m:
                        return m.group(0)
                return stripped_num
                
        # 6. Jika seluruh sel hanya sisa huruf watermark
        if re.match(r'^(?:[diogspbakthrce/\.:\s])+$', s, re.IGNORECASE):
            return ""

        return s

    @classmethod
    def is_guide_row(cls, row: List[str]) -> bool:
        non_empty = [c for c in row if c and c.strip()]
        if not non_empty:
            return True
        return all(re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', c) for c in non_empty)

    @classmethod
    def _detect_metadata(cls, pdf: pdfplumber.PDF, filename: str, prov_hint: str, kab_hint: str) -> Tuple[str, str, str, str]:
        # 1. Tahun
        year_match = re.search(r'(20\d{2}|19\d{2})', filename)
        year = year_match.group(1) if year_match else "2026"

        # 2. Kecamatan
        kec_match = re.search(r'Kecamatan\s+([A-Za-z0-9\s]+?)(?=\s+Dalam\s+Angka|\s+\d{4}|$)', filename, re.IGNORECASE)
        kecamatan = kec_match.group(1).strip() if kec_match else "Kecamatan_Unknown"

        # 3. Kabupaten & Provinsi
        provinsi = prov_hint if prov_hint and prov_hint != "Provinsi_Umum" else "Provinsi_Lainnya"
        kabupaten = kab_hint if kab_hint and kab_hint != "Kabupaten_Umum" else None

        if not kabupaten:
            for p_idx in range(min(10, len(pdf.pages))):
                try:
                    page_text = pdf.pages[p_idx].extract_text() or ""
                    m1 = re.search(r'(?:BPS|Statistik)\s+(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?:\.|\n|,|\s+Regency|\s+Municipality|$)', page_text, re.IGNORECASE)
                    if m1:
                        raw_kab = f"{m1.group(1).title()} {m1.group(2).strip().title()}"
                        kabupaten = re.sub(r'\s+[A-Za-z]$', '', raw_kab).strip()
                        break
                except Exception:
                    continue

        if not kabupaten:
            kabupaten = "Kabupaten_Lainnya"

        return provinsi, kabupaten, kecamatan, year

    @classmethod
    def _extract_title_and_info(cls, page_text: str) -> Tuple[str, str, str, str]:
        if not page_text:
            return "", "Tabel Statistik", "Umum", ""

        lines = [re.sub(r'\s+', ' ', l).strip() for l in page_text.split('\n') if l.strip()]
        table_num, title_text, sector, source = "", "", "Umum", ""

        for l in lines[:4]:
            u_line = l.upper()
            if "GEOGRAFI" in u_line or "IKLIM" in u_line:
                sector = "1_Geografi_Iklim"
                break
            elif "PEMERINTAH" in u_line:
                sector = "2_Pemerintahan"
                break
            elif "PENDUDUK" in u_line or "TENAGA KERJA" in u_line:
                sector = "3_Penduduk"
                break
            elif "SOSIAL" in u_line or "KESEJAHTERAAN" in u_line or "PENDIDIKAN" in u_line or "KESEHATAN" in u_line or "AGAMA" in u_line:
                sector = "4_Sosial"
                break
            elif "PERTANIAN" in u_line or "PETERNAKAN" in u_line or "PERIKANAN" in u_line or "KEHUTANAN" in u_line:
                sector = "5_Pertanian"
                break
            elif "PERDAGANGAN" in u_line or "ENERGI" in u_line or "HOTEL" in u_line or "KOPERASI" in u_line or "INDUSTRI" in u_line:
                sector = "6_Energi_Perdagangan"
                break
            elif "TRANSPORTASI" in u_line or "KOMUNIKASI" in u_line or "PERHUBUNGAN" in u_line:
                sector = "7_Transportasi_Lainnya"
                break

        for i, l in enumerate(lines):
            if re.search(r'^(Sumber|Source):', l, re.IGNORECASE):
                source = cls.clean_cell(l)
            
            m = re.match(r'^(?:Lanjutan\s+)?(?:Tabel|Table)\s+(?:([0-9\.]+)\s+)?(.*)', l, re.IGNORECASE)
            if m:
                t_num = m.group(1) or ""
                t_body = m.group(2) or ""

                collected = [t_body] if t_body else []
                for j in range(i + 1, min(i + 4, len(lines))):
                    nxt = lines[j]
                    if re.match(r'^[0-9\.]+$', nxt) and not t_num:
                        t_num = nxt
                        continue
                    if re.match(r'^(Table|Sumber|Source|\(\d+\)|[A-Z\s]{4,}$)', nxt, re.IGNORECASE):
                        break
                    if nxt.startswith('Nama ') or nxt.startswith('Gampong ') or nxt.startswith('Desa '):
                        break
                    collected.append(nxt)

                table_num = t_num.strip()
                title_text = cls.clean_cell(" ".join(collected).strip())

        if table_num and table_num[0] in cls.SECTORS_MAP:
            sector = cls.SECTORS_MAP[table_num[0]]

        if not title_text:
            title_text = "Tabel Statistik"

        return table_num, title_text, sector, source

    @classmethod
    def parse_document(cls, file_stream: io.BytesIO, file_id: str, filename: str, prov_hint: str = "", kab_hint: str = "") -> DocumentStatsResult:
        tables: List[StatTable] = []

        with pdfplumber.open(file_stream) as pdf:
            total_pages = len(pdf.pages)
            provinsi, kabupaten, kecamatan, year = cls._detect_metadata(pdf, filename, prov_hint, kab_hint)

            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""

                raw_tables = page.extract_tables()
                if not raw_tables:
                    continue

                table_num, table_title, sector, source = cls._extract_title_and_info(page_text)

                for t_idx, raw_tbl in enumerate(raw_tables):
                    if not raw_tbl or len(raw_tbl) < 2:
                        continue

                    cleaned_grid = []
                    for row in raw_tbl:
                        cleaned_row = [cls.clean_cell(c) for c in row]
                        cleaned_grid.append(cleaned_row)

                    if not cleaned_grid:
                        continue

                    header_row = cleaned_grid[0]
                    data_start_idx = 1

                    if len(cleaned_grid) > 1 and cls.is_guide_row(cleaned_grid[1]):
                        data_start_idx = 2
                    elif len(cleaned_grid) > 2 and cls.is_guide_row(cleaned_grid[2]):
                        combined_headers = []
                        for h0, h1 in zip(cleaned_grid[0], cleaned_grid[1]):
                            h_comb = f"{h0} {h1}".strip() if h0 != h1 else h0
                            combined_headers.append(h_comb or "Kolom")
                        header_row = combined_headers
                        data_start_idx = 3

                    clean_headers = []
                    for c_i, h in enumerate(header_row):
                        clean_h = cls.clean_cell(h)
                        clean_headers.append(clean_h if clean_h else f"Kolom_{c_i+1}")

                    data_rows = []
                    last_col0 = ""
                    for r in cleaned_grid[data_start_idx:]:
                        if cls.is_guide_row(r) or not any(r):
                            continue
                        if len(r) > 0 and re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', r[0]):
                            continue

                        if len(r) > 0:
                            if r[0]:
                                last_col0 = r[0]
                            elif last_col0 and any(r[1:]):
                                r[0] = last_col0

                        data_rows.append(r)

                    if data_rows:
                        tables.append(StatTable(
                            table_id=f"{file_id}_p{page_num}_t{t_idx+1}",
                            table_number=table_num,
                            title=table_title,
                            sector=sector,
                            page_number=page_num,
                            headers=clean_headers,
                            rows=data_rows,
                            source=source
                        ))

        return DocumentStatsResult(
            file_id=file_id,
            filename=filename,
            provinsi=provinsi,
            kabupaten_kota=kabupaten,
            kecamatan=kecamatan,
            year=year,
            total_pages=total_pages,
            tables=tables
        )


# ==============================================================================
# 5. INCREMENTAL REAL-TIME EXCEL EXPORTER (PER-FILE APPEND TO DISK)
# ==============================================================================
class IncrementalKabupatenExcelExporter:
    """
    Menyimpan hasil ekstraksi secara LINEAR & REAL-TIME:
    - Begitu 1 PDF kecamatan selesai -> Langsung disimpan ke file .xlsx Kabupaten di disk.
    - Menambahkan baris secara realtime ke sheet Data_Visualisasi, Katalog_Tabel, dan Sektor terkait.
    """

    def __init__(self, output_dir: str = "output_kabupaten"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        self.fill_header = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        
        self.font_table_banner = Font(name="Segoe UI", size=11, bold=True, color="1F4E78")
        self.fill_table_header = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        
        self.font_data = Font(name="Segoe UI", size=10)
        self.border_thin = Border(
            left=Side(style='thin', color='E0E0E0'),
            right=Side(style='thin', color='E0E0E0'),
            top=Side(style='thin', color='E0E0E0'),
            bottom=Side(style='thin', color='E0E0E0')
        )

    def _sanitize(self, name: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|]', '_', name).strip()
        return re.sub(r'\s+', '_', clean)

    def get_output_path(self, provinsi: str, kabupaten: str) -> str:
        safe_p = self._sanitize(provinsi)
        safe_k = self._sanitize(kabupaten)
        return os.path.join(self.output_dir, f"{safe_p}_{safe_k}.xlsx")

    def _get_or_create_workbook(self, xlsx_path: str) -> openpyxl.Workbook:
        if os.path.exists(xlsx_path):
            try:
                return openpyxl.load_workbook(xlsx_path)
            except Exception:
                pass

        wb = openpyxl.Workbook()
        ws_catalog = wb.active
        ws_catalog.title = "Katalog_Tabel"
        catalog_headers = ["No", "Provinsi", "Kabupaten", "Kecamatan", "Tahun", "Sektor", "Nomor Tabel", "Judul Tabel", "Halaman", "Jumlah Baris Data"]
        self._setup_headers(ws_catalog, catalog_headers)

        ws_vis = wb.create_sheet(title="Data_Visualisasi")
        vis_headers = ["Provinsi", "Kabupaten", "Kecamatan", "Tahun", "Sektor", "Nomor_Tabel", "Judul_Tabel", "Uraian_Indikator", "Variabel_Kolom", "Nilai_Statistik"]
        self._setup_headers(ws_vis, vis_headers)

        return wb

    def append_document(self, doc: DocumentStatsResult) -> str:
        """Menambahkan data 1 dokumen kecamatan ke dalam workbook Kabupaten secara real-time."""
        xlsx_path = self.get_output_path(doc.provinsi, doc.kabupaten_kota)
        wb = self._get_or_create_workbook(xlsx_path)

        ws_catalog = wb["Katalog_Tabel"]
        ws_vis = wb["Data_Visualisasi"]

        # Tulis setiap tabel dari dokumen ini
        for tbl in doc.tables:
            # 1. Tambah ke Katalog
            cat_no = ws_catalog.max_row
            ws_catalog.append([
                cat_no,
                doc.provinsi,
                doc.kabupaten_kota,
                doc.kecamatan,
                doc.year,
                tbl.sector,
                tbl.table_number or "-",
                tbl.title,
                tbl.page_number,
                len(tbl.rows)
            ])
            curr_cat_row = ws_catalog.max_row
            for col_i in range(1, 11):
                cell = ws_catalog.cell(row=curr_cat_row, column=col_i)
                cell.font = self.font_data
                cell.border = self.border_thin

            # 2. Tambah ke Data_Visualisasi
            if len(tbl.headers) >= 2:
                for r in tbl.rows:
                    row_key = r[0] if len(r) > 0 else "Total"
                    if re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', str(row_key)):
                        continue
                    
                    for c_idx in range(1, len(tbl.headers)):
                        if c_idx < len(r):
                            var_name = tbl.headers[c_idx]
                            val_stat = r[c_idx]
                            if re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', str(var_name)) or re.match(r'^\s*\(?\s*\d+\s*\)?\.?\s*$', str(val_stat)):
                                continue
                            
                            if val_stat != "":
                                ws_vis.append([
                                    doc.provinsi,
                                    doc.kabupaten_kota,
                                    doc.kecamatan,
                                    doc.year,
                                    tbl.sector,
                                    tbl.table_number or "-",
                                    tbl.title,
                                    str(row_key),
                                    str(var_name),
                                    val_stat
                                ])
                                curr_vis_row = ws_vis.max_row
                                for col_i in range(1, 11):
                                    c_elem = ws_vis.cell(row=curr_vis_row, column=col_i)
                                    c_elem.font = self.font_data
                                    c_elem.border = self.border_thin

            # 3. Tambah ke Sektor Sheet
            sec_title = tbl.sector[:31]
            if sec_title not in wb.sheetnames:
                ws_sec = wb.create_sheet(title=sec_title)
            else:
                ws_sec = wb[sec_title]

            # Banner Judul Tabel
            t_label = f"[{doc.kecamatan} - {doc.year}] {('Tabel ' + tbl.table_number + ': ') if tbl.table_number else ''}{tbl.title} (Hal. {tbl.page_number})"
            ws_sec.append([t_label])
            banner_cell = ws_sec.cell(row=ws_sec.max_row, column=1)
            banner_cell.font = self.font_table_banner

            # Header Kolom
            ws_sec.append(tbl.headers)
            h_row_idx = ws_sec.max_row
            for col_i in range(1, len(tbl.headers) + 1):
                c_elem = ws_sec.cell(row=h_row_idx, column=col_i)
                c_elem.font = self.font_header
                c_elem.fill = self.fill_table_header
                c_elem.border = self.border_thin
                c_elem.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Baris Data
            for r in tbl.rows:
                ws_sec.append(r)
                d_row_idx = ws_sec.max_row
                for col_i in range(1, len(tbl.headers) + 1):
                    c_elem = ws_sec.cell(row=d_row_idx, column=col_i)
                    c_elem.font = self.font_data
                    c_elem.border = self.border_thin
                    if col_i > 1 and re.match(r'^-?\d+(?:[\.,]\d+)?$', str(c_elem.value or '')):
                        c_elem.alignment = Alignment(horizontal="right")

            ws_sec.append([])

        # Auto-adjust lebar kolom
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col[:100]:
                    if cell.value:
                        lines = str(cell.value).split('\n')
                        max_len = max(max_len, len(lines[0]))
                adjusted_width = min(max(max_len + 3, 12), 65)
                sheet.column_dimensions[col_letter].width = adjusted_width

        # Simpan langsung ke file di disk
        wb.save(xlsx_path)
        return xlsx_path

    def _setup_headers(self, ws, headers: List[str]):
        ws.append(headers)
        ws.row_dimensions[1].height = 28
        ws.freeze_panes = "A2"
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = self.font_header
            cell.fill = self.fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.border_thin


# ==============================================================================
# 6. MAIN ENGINE (REAL-TIME LINEAR PROCESSING)
# ==============================================================================
def run_supex(
    target_url_or_path: str = "https://drive.google.com/drive/folders/1BLO-ZkOvEvo4mlVQVfTU5I5GGU1q791i?usp=sharing",
    output_dir: str = "output_kabupaten",
    force_rescan: bool = False,
    worker_id: int = 1,
    total_workers: int = 1
):
    if worker_id < 1 or total_workers < 1 or worker_id > total_workers:
        print(f"[!] Error: Nilai worker ({worker_id}) harus di antara 1 dan total worker ({total_workers}).")
        return

    tracker_file = f"progress_tracker_w{worker_id}.json" if total_workers > 1 else "progress_tracker.json"
    tracker = ProgressTracker(tracker_file=tracker_file)
    streamer = UniversalStreamer(target_url_or_path, cache_file="gdrive_file_index.json")
    exporter = IncrementalKabupatenExcelExporter(output_dir=output_dir)

    print("\n" + "=" * 70, flush=True)
    if total_workers > 1:
        print(f"   SUPEX - BPS STATISTICAL EXTRACTOR (WORKER {worker_id} / {total_workers})", flush=True)
    else:
        print("   SUPEX - BPS STATISTICAL EXTRACTOR (SINGLE WORKER MODE)", flush=True)
    print("=" * 70, flush=True)
    print(f"[*] Sumber Data   : {target_url_or_path}", flush=True)
    print(f"[*] Folder Output : {output_dir}/", flush=True)
    print(f"[*] Worker ID     : {worker_id} dari total {total_workers} Worker", flush=True)
    print(f"[*] Tracker File  : {tracker_file}", flush=True)
    print(f"[*] Mode Simpan   : Real-Time Incremental (Langsung Tulis per File)", flush=True)
    print("=" * 70 + "\n", flush=True)

    # 1. Listing File (Memuat dari cache instan)
    all_files = streamer.list_files(force_rescan=force_rescan)
    if not all_files:
        print("[!] Tidak ada file yang ditemukan untuk diproses.", flush=True)
        return

    # 2. Kelompokkan File per Kabupaten
    kabupaten_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for f in all_files:
        p = f.get("provinsi", "Provinsi_Umum")
        k = f.get("kabupaten", "Kabupaten_Umum")
        kabupaten_map.setdefault((p, k), []).append(f)

    # Urutkan secara deterministik agar semua worker memiliki susunan index yang persis sama
    sorted_kabupatens = sorted(kabupaten_map.items(), key=lambda x: (x[0][0], x[0][1]))
    total_all_kabupatens = len(sorted_kabupatens)

    # Pembagian Sharding Modulo: (global_index - 1) % total_workers == (worker_id - 1)
    worker_kabupatens = [
        (global_idx, item) for global_idx, item in enumerate(sorted_kabupatens, 1)
        if (global_idx - 1) % total_workers == (worker_id - 1)
    ]

    total_processed_files = len(tracker.state.get("completed_files", {}))
    print(f"[*] Total Database   : {total_all_kabupatens} Kabupaten/Kota ({len(all_files):,} file PDF)", flush=True)
    print(f"[*] Porsi Worker Ini : {len(worker_kabupatens)} Kabupaten/Kota", flush=True)
    print(f"[*] Global Progress  : {total_processed_files:,} / {len(all_files):,} file PDF selesai ({total_processed_files/max(len(all_files), 1)*100:.1f}%)\n", flush=True)

    # 3. Iterasi per Kabupaten untuk Worker ini
    for local_idx, (global_idx, ((prov, kab), file_group)) in enumerate(worker_kabupatens, 1):
        kab_key = f"{prov}_{kab}"
        expected_output = exporter.get_output_path(prov, kab)

        # Cek apakah seluruh file di kabupaten ini sudah selesai
        all_files_done = all(tracker.is_file_completed(f["id"]) for f in file_group)
        if all_files_done and os.path.exists(expected_output):
            print(f"[W{worker_id}] [{local_idx}/{len(worker_kabupatens)}] [Global #{global_idx}] [✓ SUDAH SELESAI] {prov} ➔ {kab} (Dilewati)", flush=True)
            continue

        print("-" * 70, flush=True)
        print(f"[W{worker_id}] [{local_idx}/{len(worker_kabupatens)}] (Global #{global_idx}/{total_all_kabupatens}) MEMPROSES: {prov.upper()} ➔ {kab.upper()}", flush=True)
        print(f"     Target Dokumen : {len(file_group)} file PDF Kecamatan", flush=True)
        print(f"     Target Output  : {os.path.basename(expected_output)}", flush=True)
        print("-" * 70, flush=True)

        for f_idx, f_info in enumerate(file_group, 1):
            file_id = f_info["id"]
            fname = f_info["name"]

            # Skip per file jika file ini sudah pernah disimpan
            if tracker.is_file_completed(file_id):
                print(f"  [{f_idx:02d}/{len(file_group):02d}] ⏭️ [SKIP] {fname} (Sudah ada di Excel)", flush=True)
                continue

            # Deteksi preview nama kecamatan & tahun
            kec_preview = re.search(r'Kecamatan\s+([A-Za-z0-9\s]+?)(?=\s+Dalam\s+Angka|\s+\d{4}|$)', fname, re.IGNORECASE)
            kec_name = kec_preview.group(1).strip() if kec_preview else "Kecamatan"
            year_preview = re.search(r'(20\d{2}|19\d{2})', fname)
            yr_str = f" ({year_preview.group(1)})" if year_preview else ""

            t0 = time.time()
            try:
                # 1. Stream PDF ke RAM
                pdf_stream = streamer.stream_to_memory(f_info)
                
                # 2. Ekstrak Tabel Statistik
                doc_res = BPSStatisticalParser.parse_document(
                    file_stream=pdf_stream,
                    file_id=file_id,
                    filename=fname,
                    prov_hint=prov,
                    kab_hint=kab
                )
                
                pdf_stream.close()
                del pdf_stream

                # 3. REAL-TIME APPEND: Simpan langsung ke file Excel di disk
                if doc_res.tables:
                    exporter.append_document(doc_res)

                # 4. Catat status selesai di progress tracker
                tracker.mark_file_completed(file_id, fname)
                elapsed = time.time() - t0

                print(f"  [{f_idx:02d}/{len(file_group):02d}] ✓ [DONE & SAVED] Kec. {doc_res.kecamatan}{yr_str} -> {len(doc_res.tables)} tabel ({elapsed:.1f}s)", flush=True)

            except Exception as e:
                print(f"  [{f_idx:02d}/{len(file_group):02d}] ✗ [ERROR] {fname} -> {str(e)}", flush=True)
                tracker.log_failure(f_info, str(e))

        # Tandai Kabupaten selesai
        tracker.mark_kabupaten_completed(kab_key)
        print(f"  🎉 [KABUPATEN SELESAI] {os.path.basename(expected_output)}\n", flush=True)

    print("\n" + "=" * 70, flush=True)
    print(f"   🎉 [SELESAI] SELURUH PORSI TUGAS WORKER {worker_id} DARI {total_workers} TELAH TUNTAS!", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SUPEX - BPS Statistical Extractor (Multi-Terminal Sharding)")
    parser.add_argument("--worker", type=int, default=1, help="Nomor worker ini (1, 2, 3, dst). Default: 1")
    parser.add_argument("--total", type=int, default=1, help="Total seluruh worker yang dijalankan. Default: 1")
    parser.add_argument("--source", type=str, default="https://drive.google.com/drive/folders/1BLO-ZkOvEvo4mlVQVfTU5I5GGU1q791i?usp=sharing", help="Link Google Drive atau folder lokal")
    parser.add_argument("--output", type=str, default="output_kabupaten", help="Folder tujuan output Excel")
    parser.add_argument("--force-rescan", action="store_true", help="Paksa scan ulang Google Drive (abaikan cache)")

    args = parser.parse_args()

    run_supex(
        target_url_or_path=args.source,
        output_dir=args.output,
        force_rescan=args.force_rescan,
        worker_id=args.worker,
        total_workers=args.total
    )
