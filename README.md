# SUPEX - BPS Statistical Extractor

Sistem otomasi ekstraksi data tabel statistik dari publikasi PDF BPS (*Kecamatan Dalam Angka*) dari Google Drive / folder lokal, yang dibersihkan dari watermark dan dikonversi secara real-time ke format Excel (`.xlsx`) per Kabupaten/Kota.

---

## 🚀 Fitur Utama
- **In-Memory PDF Streaming**: Mengalirkan PDF langsung ke RAM tanpa harus mengunduh ribuan file ke penyimpanan lokal.
- **Smart Data Cleaner**: Membersihkan watermark vertikal BPS, menormalisasi baris panduan penomoran `(1), (2)`, dan merapikan header kolom multi-tingkat.
- **Incremental Real-Time Exporter**: Data langsung ditulis ke file `.xlsx` per Kabupaten begitu 1 PDF kecamatan selesai.
  - Sheet `Katalog_Tabel`: Indeks metadata seluruh tabel.
  - Sheet `Data_Visualisasi`: Data bentuk *long-format* (siap analisis BI).
  - Sheet Sektor (`1_Geografi_Iklim`, `3_Penduduk`, dst): Tampilan tabel asli.
- **Multi-Worker Sharding**: Pembagian kerja modular jika ingin dijalankan paralel di beberapa terminal atau worker server.
- **Progress Tracker & Resumable**: Jika proses terputus, sistem otomatis melewati (*skip*) file yang sudah berhasil disimpan.

---

## 🛠️ Instalasi

1. Clone repository:
   ```bash
   git clone https://github.com/Karnodinata/supex.git
   cd supex
   ```

2. Buat virtual environment (opsional namun disarankan):
   ```bash
   python -m venv venv
   # Di Windows:
   .\venv\Scripts\activate
   # Di Linux/macOS:
   source venv/bin/activate
   ```

3. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Cara Menjalankan (CLI)

### Single Worker (Standar)
```bash
python supex.py
```

### Multi-Worker / Paralel (Contoh: 4 Terminal)
Buka 4 terminal berbeda dan jalankan masing-masing:
```bash
# Terminal 1
python supex.py --worker 1 --total 4

# Terminal 2
python supex.py --worker 2 --total 4

# Terminal 3
python supex.py --worker 3 --total 4

# Terminal 4
python supex.py --worker 4 --total 4
```

---

## 🌐 Rencana Pengembangan Web UI
Untuk pengembangan antarmuka web:
- Direkomendasikan menggunakan **[Streamlit](https://streamlit.io/)** (`pip install streamlit`) atau **FastAPI + Vue/React**.
- Alur yang dapat diintegrasikan:
  1. Pilih Provinsi / Kabupaten dari file cache `gdrive_file_index.json`.
  2. Tombol *Start Extraction* dengan *real-time progress bar*.
  3. Pratinjau tabel hasil ekstraksi langsung di halaman web.
  4. Tombol *Download Excel* untuk file hasil ekstraksi di folder `output_kabupaten/`.
