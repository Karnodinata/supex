# SUPEX - BPS Statistical PDF to Excel Real-Time Extractor

SUPEX (Statistical Universal PDF Extractor) adalah sistem otomasi end-to-end berbasis Python untuk mengekstrak, membersihkan, dan menstandarisasi data tabel statistik dari ribuan publikasi PDF resmi Badan Pusat Statistik (BPS)—khususnya seri publikasi tahunan "Kecamatan Dalam Angka" dari 34 Provinsi di Indonesia—langsung ke dalam format spreadsheet Excel (.xlsx) per Kabupaten/Kota.

---

## Fitur Utama

1. **In-Memory Streaming (Zero Local PDF Storage)**
   - Mengambil data file PDF langsung dari Google Drive via HTTP stream ke memori virtual RAM (io.BytesIO).
   - Hard disk tidak terbebani file sampah PDF berukuran puluhan hingga ratusan Gigabyte. Begitu tabel diekstrak, RAM langsung dibebaskan.

2. **Smart Watermark & Text Cleaner**
   - Membersihkan watermark vertikal khas dokumen BPS (diogspbakthrce) yang sering menempel pada angka dan teks.
   - Menghapus baris panduan penomoran kolom standar BPS seperti (1), (2), (3).
   - Menggabungkan sel baris header atas dan bawah (multi-level headers) menjadi kolom terpadu.

3. **Incremental Real-Time Exporter**
   - Menyimpan hasil secara linier dan bertahap per file kecamatan langsung ke file .xlsx Kabupaten terkait di folder output_kabupaten/.
   - Jika proses terhenti di tengah jalan, data yang sudah masuk ke Excel tidak akan hilang atau corrupt.

4. **Multi-Worker Sharding (Parallel Execution)**
   - Mendukung eksekusi paralel di banyak terminal atau mesin worker menggunakan algoritma sharding modulo deterministik:
     $$\text{index} \pmod{\text{total\_workers}} == (\text{worker\_id} - 1)$$
   - Antar worker otomatis memproses kabupaten yang berbeda tanpa perlu database server pusat.

5. **State Tracking & Resumability**
   - Status setiap dokumen dicatat ke progress_tracker*.json.
   - Sistem otomatis melewati (skip) file atau kabupaten yang telah selesai diekstrak saat script dijalankan kembali.

---

## Struktur Output File Excel (.xlsx)

Setiap Kabupaten/Kota menghasilkan 1 file Excel (misal: Jawa_Timur_Kab._Kediri.xlsx) yang memiliki struktur sheet:

| Nama Sheet | Deskripsi & Fungsi |
| :--- | :--- |
| **Katalog_Tabel** | Indeks daftar isi seluruh tabel statistik yang berhasil diekstrak (Kecamatan, Tahun, Sektor, Nomor Tabel, Judul Tabel, Halaman, dan Jumlah Baris). |
| **Data_Visualisasi** | Format tabel ternormalisasi (unpivoted / long format) berisi kolom [Provinsi, Kabupaten, Kecamatan, Tahun, Sektor, Nomor_Tabel, Judul_Tabel, Uraian_Indikator, Variabel_Kolom, Nilai_Statistik]. Sangat cocok langsung dihubungkan ke Power BI, Tableau, Streamlit, atau database SQL. |
| **Sheet Sektor** *(misal 3_Penduduk, 5_Pertanian)* | Menampilkan tabel asli lengkap dengan banner judul, header kolom bergradasi biru, perataan angka, border sel, dan penyesuaian lebar kolom otomatis (auto-fit column width). |

---

## Persyaratan & Instalasi

### 1. Prasyarat Sistem
* Python 3.8 atau versi yang lebih baru.
* Koneksi internet (untuk streaming dokumen dari Google Drive).

### 2. Langkah Instalasi

1. Clone repository ke komputer lokal:
   ```bash
   git clone https://github.com/Karnodinata/supex.git
   cd supex
   ```

2. Buat dan aktifkan virtual environment (opsional namun sangat disarankan):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependensi library yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

---

## Panduan Menjalankan Sistem

### A. Mode Tunggal (Single Worker)
Untuk menjalankan ekstraksi secara berurutan pada 1 terminal:
```bash
python supex.py
```

### B. Mode Paralel Multi-Worker (Contoh: 4 Terminal)
Untuk mempercepat ekstraksi, buka beberapa tab/jendela terminal secara bersamaan dan tentukan nomor worker-nya:

* **Terminal 1 (Worker 1):**
  ```bash
  python supex.py --worker 1 --total 4
  ```
* **Terminal 2 (Worker 2):**
  ```bash
  python supex.py --worker 2 --total 4
  ```
* **Terminal 3 (Worker 3):**
  ```bash
  python supex.py --worker 3 --total 4
  ```
* **Terminal 4 (Worker 4):**
  ```bash
  python supex.py --worker 4 --total 4
  ```

---

## Opsi Parameter CLI (supex.py)

| Argumen | Tipe | Nilai Default | Keterangan |
| :--- | :---: | :--- | :--- |
| `--worker` | int | 1 | Nomor urut worker yang sedang berjalan (1, 2, 3, dst). |
| `--total` | int | 1 | Total seluruh worker yang dialokasikan bersamaan. |
| `--source` | str | URL Google Drive BPS | URL folder Google Drive atau path direktori lokal berisi file PDF. |
| `--output` | str | output_kabupaten | Nama folder tujuan penyimpanan file Excel hasil ekstraksi. |
| `--force-rescan` | flag | False | Memaksa pemindaian ulang struktur Google Drive (mengabaikan cache). |

---

## Struktur Berkas Proyek

```text
supex/
├── .gitignore                  # File konfigurasi pengecualian file besar/temporary
├── README.md                   # Dokumentasi resmi penggunaan sistem
├── requirements.txt            # Daftar library Python (pdfplumber, openpyxl, dll)
├── supex.py                    # Core engine ekstraktor & runner CLI
├── gdrive_file_index.json      # Cache lokal indeks 46.000+ file PDF Google Drive
├── progress_tracker*.json      # File pelacak state progres per worker
├── find_test.py                # Utilitas uji pemindaian folder Google Drive
└── output_kabupaten/           # Direktori output file Excel per Kabupaten (diabaikan git)
```

---

## Teknologi & Library yang Digunakan

* **pdfplumber**: Ekstraksi struktur tabel PDF, koordinat sel, dan teks halaman.
* **openpyxl**: Pembuatan, penulisan incremental, dan styling sheet Excel (.xlsx).
* **requests**: Pengambilan stream chunk binary file PDF dari Google Drive.
* **gdown**: Pemetaan pohon direktori dan metadata Google Drive tanpa download.
* **re (Regular Expressions)**: Algoritma pembersihan watermark, deteksi tahun publikasi, dan normalisasi tabel.
