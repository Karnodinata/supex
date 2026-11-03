import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { execFile } from 'child_process';
import ExcelJS from 'exceljs';
import { PDFParse } from 'pdf-parse';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// Multer storage
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, uploadDir),
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
        cb(null, `${uniqueSuffix}-${file.originalname}`);
    }
});
const upload = multer({
    storage,
    limits: { fileSize: 100 * 1024 * 1024 }
});

// Load template columns
let templateColumns = [];
const templatePath = path.join(__dirname, 'template_columns.json');
if (fs.existsSync(templatePath)) {
    try {
        templateColumns = JSON.parse(fs.readFileSync(templatePath, 'utf-8'));
    } catch (e) {
        console.error('Error loading template_columns.json:', e);
    }
}

const SECTORS_MAP = {
    '1': '1_Geografi_Iklim',
    '2': '2_Pemerintahan',
    '3': '3_Penduduk',
    '4': '4_Sosial',
    '5': '5_Pertanian',
    '6': '6_Energi_Perdagangan',
    '7': '7_Transportasi_Lainnya'
};

const SECTOR_TO_TEMPLATE_CATEGORIES = {
    '1_Geografi_Iklim': ['Topografi Mayoritas', 'Batas Wilayah'],
    '2_Pemerintahan': ['Pemerintahan', 'Pemilu 2024', 'DPRD'],
    '3_Penduduk': ['Pendudukan / SDM', 'Penduduk per Jenis Kelamin', 'Penduduk per Kelompok Umur'],
    '4_Sosial': ['Profil Angkatan Kerja', 'Angka IPM', 'Jumlah Penduduk Miskin'],
    '5_Pertanian': ['Ekonomi', 'PDRB per Industri', 'Harga Berlaku'],
    '6_Energi_Perdagangan': ['Pendapatan Daerah', 'Belanja Daerah', 'Ekonomi', 'PDRB per Industri'],
    '7_Transportasi_Lainnya': ['Ekonomi', 'PDRB per Industri']
};

function detectMetadata(filename, firstPagesText) {
    let year = '2024';
    const yearMatch = filename.match(/(20\d{2}|19\d{2})/);
    if (yearMatch) {
        year = yearMatch[1];
    } else {
        const yearInText = firstPagesText.match(/(20\d{2}|19\d{2})/);
        if (yearInText) year = yearInText[1];
    }

    let kecamatan = 'Kecamatan_Umum';
    const kecMatch = filename.match(/Kecamatan\s+([A-Za-z0-9\s]+?)(?=\s+Dalam\s+Angka|\s+\d{4}|$)/i);
    if (kecMatch) {
        kecamatan = kecMatch[1].trim();
    } else {
        const kecInText = firstPagesText.match(/KECAMATAN\s+([A-Z0-9\s]+?)(?=\s+DALAM\s+ANGKA|\n)/i);
        if (kecInText) kecamatan = kecInText[1].trim();
    }

    let kabupaten = 'Kabupaten_Umum';
    const kabMatch = filename.match(/(?:Kabupaten|Kab\.|Kota)\s+([A-Za-z0-9\s]+?)(?=\s+Dalam\s+Angka|\s+\d{4}|$)/i);
    if (kabMatch) {
        kabupaten = kabMatch[0].trim();
    } else {
        const kabInText = firstPagesText.match(/(?:BPS|Statistik|Pemerintah)\s+(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?:\.|\n|,|\s+Regency|\s+Municipality|$)/i);
        if (kabInText) {
            kabupaten = `${kabInText[1]} ${kabInText[2].trim()}`;
        }
    }

    let provinsi = 'Provinsi_Umum';
    const provMatch = firstPagesText.match(/Provinsi\s+([A-Za-z\s]+?)(?:\.|\n|,|$)/i);
    if (provMatch) provinsi = provMatch[1].trim();

    return { year, kecamatan, kabupaten, provinsi };
}

// 1. API: Scan PDF & list tables (dengan grouping tabel lanjutan)
app.post('/api/upload-and-scan', upload.single('pdfFile'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'File PDF wajib diunggah.' });
        }

        const filePath = req.file.path;
        const filename = req.file.originalname;
        const fileBuffer = fs.readFileSync(filePath);
        const uint8 = new Uint8Array(fileBuffer);

        const t0 = Date.now();
        const parser = new PDFParse(uint8);
        await parser.load();
        const parseResult = await parser.getText();
        const elapsedScan = Date.now() - t0;

        const pages = parseResult.pages || [];
        const totalPages = pages.length;

        const first10PagesText = pages.slice(0, 10).map(p => p.text).join('\n');
        const metadata = detectMetadata(filename, first10PagesText);
        metadata.filename = filename;
        metadata.totalPages = totalPages;
        metadata.fileId = path.basename(filePath);

        const tables = [];

        for (const p of pages) {
            const lines = p.text.split('\n').map(l => l.trim()).filter(Boolean);
            const top3 = lines.slice(0, 3).join(' ').toUpperCase();
            if (top3.includes('DAFTAR ISI') || top3.includes('DAFTAR TABEL')) {
                continue;
            }

            for (let i = 0; i < Math.min(8, lines.length); i++) {
                const line = lines[i].replace(/\s+/g, ' ').trim();
                const isCont = /(?:^|\s)(?:Lanjutan|Continued)(?:\s|$|\()/i.test(line);

                const m = line.match(/(?:(?:Lanjutan|Continued)\s+)?(?:Tabel|Table)\s*([0-9\.]+)\s*(.*)/i)
                       || line.match(/(?:Tabel|Table)\s*([0-9\.]+)\s*(?:\(?\s*(?:Lanjutan|Continued)\s*\)?)\s*(.*)/i);

                if (m) {
                    const tableNum = m[1].replace(/\.$/, '');
                    let title = m[2] ? m[2].trim() : '';

                    title = title.replace(/\(?\s*(?:Lanjutan|Continued)\s*\)?/gi, '').trim();

                    if (!title || title.length < 5) {
                        const titleLines = [];
                        for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
                            const nxt = lines[j];
                            if (/^(Table|Tabel|Sumber|Source|\(\d+\))/i.test(nxt)) break;
                            if (nxt === nxt.toUpperCase() && nxt.length > 5 && !/[0-9]/.test(nxt)) break;
                            if (nxt.startsWith('Nama ') || nxt.startsWith('Desa ') || nxt.startsWith('http')) break;
                            titleLines.push(nxt);
                        }
                        title = (title + ' ' + titleLines.join(' ')).trim();
                    }

                    if (!title) title = `Tabel ${tableNum}`;

                    const secNum = tableNum ? tableNum.split('.')[0] : '1';
                    const sector = SECTORS_MAP[secNum] || 'Umum';
                    const matchedCategories = SECTOR_TO_TEMPLATE_CATEGORIES[sector] || [];

                    // Cek jika tabel ini adalah kelanjutan dari tabel sebelumnya
                    const existingTable = tables.find(t => t.tableNumber === tableNum);
                    if (existingTable && (isCont || p.num === existingTable.pages[existingTable.pages.length - 1] + 1)) {
                        if (!existingTable.pages.includes(p.num)) {
                            existingTable.pages.push(p.num);
                            existingTable.isContinued = true;
                            existingTable.pageCount = existingTable.pages.length;
                        }
                    } else if (!existingTable) {
                        tables.push({
                            id: `tbl_${p.num}_${tableNum.replace(/\./g, '_')}`,
                            tableNumber: tableNum,
                            title: title.replace(/\s+/g, ' '),
                            sector,
                            pageNumber: p.num,
                            pages: [p.num],
                            isContinued: false,
                            pageCount: 1,
                            matchedCategories
                        });
                    }
                    break;
                }
            }
        }

        await parser.destroy();

        return res.json({
            success: true,
            scanTimeMs: elapsedScan,
            fileId: metadata.fileId,
            metadata,
            tables,
            totalTables: tables.length
        });
    } catch (err) {
        console.error('Scan error:', err);
        return res.status(500).json({ success: false, error: err.message });
    }
});

// 2. API: Preview single or multi-page continued table
app.post('/api/preview-table', (req, res) => {
    const { fileId, tableId, pageNumber, pages } = req.body;
    if (!fileId) {
        return res.status(400).json({ success: false, error: 'fileId diperlukan.' });
    }

    const targetPages = Array.isArray(pages) && pages.length > 0 
        ? pages 
        : (pageNumber ? [pageNumber] : []);

    if (targetPages.length === 0) {
        return res.status(400).json({ success: false, error: 'Target halaman tidak valid.' });
    }

    const pdfPath = path.join(uploadDir, fileId);
    if (!fs.existsSync(pdfPath)) {
        return res.status(404).json({ success: false, error: 'File PDF tidak ditemukan di server.' });
    }

    const tKey = tableId || `preview_${targetPages[0]}`;
    const spec = { [tKey]: targetPages };

    const pythonScript = path.join(__dirname, 'extract_worker.py');
    execFile('python', ['-u', pythonScript, pdfPath, JSON.stringify(spec)], (error, stdout, stderr) => {
        if (error) {
            console.error('Preview exec error:', error, stderr);
            return res.status(500).json({ success: false, error: stderr || error.message });
        }
        try {
            const data = JSON.parse(stdout);
            if (!data.success) {
                return res.status(500).json({ success: false, error: data.error });
            }
            const tblData = data.results[tKey];
            if (!tblData) {
                return res.json({
                    success: true,
                    table: { headers: [], rows: [], totalRows: 0, totalCols: 0, pagesIncluded: targetPages }
                });
            }
            return res.json({
                success: true,
                table: {
                    headers: tblData.headers,
                    rows: tblData.rows,
                    totalRows: tblData.totalRows,
                    totalCols: tblData.totalCols,
                    pagesIncluded: tblData.pagesIncluded,
                    isContinued: targetPages.length > 1
                }
            });
        } catch (e) {
            console.error('JSON parse error:', e, stdout);
            return res.status(500).json({ success: false, error: 'Gagal parse data dari PDF worker.' });
        }
    });
});

// 3. API: Export Excel with full multi-page table merging & template
app.post('/api/export-excel', async (req, res) => {
    try {
        const { fileId, selectedTables, metadata, customFilename } = req.body;
        if (!fileId || !selectedTables || !Array.isArray(selectedTables) || selectedTables.length === 0) {
            return res.status(400).json({ success: false, error: 'Pilih minimal 1 tabel untuk diexport.' });
        }

        const pdfPath = path.join(uploadDir, fileId);
        if (!fs.existsSync(pdfPath)) {
            return res.status(404).json({ success: false, error: 'File PDF tidak ditemukan di server.' });
        }

        // Build specs for worker: { [t.id]: t.pages }
        const specs = {};
        selectedTables.forEach(t => {
            const pages = Array.isArray(t.pages) && t.pages.length > 0 ? t.pages : [t.pageNumber];
            specs[t.id] = pages;
        });

        const pythonScript = path.join(__dirname, 'extract_worker.py');
        execFile('python', ['-u', pythonScript, pdfPath, JSON.stringify(specs)], async (error, stdout, stderr) => {
            if (error) {
                console.error('Export exec error:', error, stderr);
                return res.status(500).json({ success: false, error: stderr || error.message });
            }

            let extractedData;
            try {
                const parsed = JSON.parse(stdout);
                if (!parsed.success) {
                    return res.status(500).json({ success: false, error: parsed.error });
                }
                extractedData = parsed.results || {};
            } catch (e) {
                return res.status(500).json({ success: false, error: 'Gagal memproses data tabel terpilih.' });
            }

            const wb = new ExcelJS.Workbook();
            wb.creator = 'BPS Data Parser Web';
            wb.created = new Date();

            // 1. Sheet 1: Master Template BPS (128 kolom)
            const wsTemplate = wb.addWorksheet('Template_Standar_BPS');
            const catRowValues = [];
            const fieldRowValues = [];

            templateColumns.forEach(col => {
                catRowValues.push(col.category || '');
                fieldRowValues.push(col.field || '');
            });

            wsTemplate.addRow(catRowValues);
            wsTemplate.addRow(fieldRowValues);

            const headerFillNavy = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1F4E78' } };
            const headerFillSub = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2F5597' } };
            const headerFont = { name: 'Segoe UI', size: 10, bold: true, color: { argb: 'FFFFFFFF' } };
            const borderThin = {
                top: { style: 'thin', color: { argb: 'FFE0E0E0' } },
                bottom: { style: 'thin', color: { argb: 'FFE0E0E0' } },
                left: { style: 'thin', color: { argb: 'FFE0E0E0' } },
                right: { style: 'thin', color: { argb: 'FFE0E0E0' } }
            };

            const row1 = wsTemplate.getRow(1);
            row1.font = headerFont;
            row1.fill = headerFillNavy;
            row1.height = 24;
            row1.alignment = { vertical: 'middle', horizontal: 'center' };

            const row2 = wsTemplate.getRow(2);
            row2.font = headerFont;
            row2.fill = headerFillSub;
            row2.height = 28;
            row2.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };

            let startCol = 1;
            for (let c = 1; c <= templateColumns.length; c++) {
                const currentCat = templateColumns[c - 1]?.category || '';
                const nextCat = templateColumns[c]?.category || '';
                if (currentCat && currentCat !== nextCat && c > startCol) {
                    try {
                        wsTemplate.mergeCells(1, startCol, 1, c);
                    } catch (e) {}
                    startCol = c + 1;
                } else if (!currentCat) {
                    startCol = c + 1;
                }
            }

            const sampleDataRow = new Array(templateColumns.length).fill('');
            sampleDataRow[0] = '1';
            sampleDataRow[1] = (metadata && metadata.provinsi) || 'ACEH';
            sampleDataRow[2] = (metadata && (metadata.kabupaten || metadata.kecamatan)) || 'WILAYAH';
            wsTemplate.addRow(sampleDataRow);

            for (let c = 1; c <= templateColumns.length; c++) {
                const cellVal = fieldRowValues[c - 1] || '';
                wsTemplate.getColumn(c).width = Math.min(Math.max(cellVal.length + 3, 14), 45);
            }

            // 2. Sheets untuk setiap tabel yang dipilih (termasuk lanjutan yang sudah digabung utuh)
            selectedTables.forEach((t) => {
                const tbl = extractedData[t.id];
                if (!tbl || !tbl.headers || tbl.headers.length === 0) return;

                const pageRangeStr = tbl.pagesIncluded.length > 1
                    ? `Hal_${tbl.pagesIncluded[0]}-${tbl.pagesIncluded[tbl.pagesIncluded.length - 1]}`
                    : `Hal_${tbl.pagesIncluded[0]}`;

                const cleanNum = (t.tableNumber || 'Tabel').replace(/[^0-9A-Za-z]/g, '_');
                const safeSheetName = `${cleanNum}_${pageRangeStr}`.substring(0, 31);

                const wsTable = wb.addWorksheet(safeSheetName);

                // Banner Judul Tabel
                const contNotice = tbl.pagesIncluded.length > 1 ? ` (Tabel Lanjutan Tergabung ${tbl.pagesIncluded.length} Halaman)` : '';
                wsTable.addRow([`[${t.tableNumber ? 'Tabel ' + t.tableNumber + ': ' : ''}${t.title}] (${pageRangeStr.replace('_', ' ')})${contNotice}`]);
                const bannerRow = wsTable.getRow(1);
                bannerRow.font = { name: 'Segoe UI', size: 12, bold: true, color: { argb: 'FF1F4E78' } };
                bannerRow.height = 24;

                // Header Baris
                wsTable.addRow(tbl.headers);
                const hRow = wsTable.getRow(2);
                hRow.font = headerFont;
                hRow.fill = headerFillNavy;
                hRow.height = 26;
                hRow.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };

                // Baris Data Gabungan
                tbl.rows.forEach(r => {
                    const rowObj = wsTable.addRow(r);
                    rowObj.font = { name: 'Segoe UI', size: 10 };
                    rowObj.eachCell((cell, colNum) => {
                        cell.border = borderThin;
                        if (colNum > 1 && /^-?\d+([.,]\d+)?$/.test(String(cell.value || '').trim())) {
                            cell.alignment = { horizontal: 'right' };
                        }
                    });
                });

                // Auto-adjust lebar kolom
                tbl.headers.forEach((h, hIdx) => {
                    let maxLen = (h || '').length;
                    tbl.rows.slice(0, 40).forEach(r => {
                        const val = String(r[hIdx] || '');
                        if (val.length > maxLen) maxLen = val.length;
                    });
                    wsTable.getColumn(hIdx + 1).width = Math.min(Math.max(maxLen + 4, 12), 55);
                });
            });

            let downloadName = customFilename;
            if (!downloadName) {
                const yr = metadata?.year || '2024';
                const daerah = (metadata?.kecamatan || metadata?.kabupaten || 'Daerah')
                    .replace(/[^A-Za-z0-9]/g, '_');
                const varCount = selectedTables.length;
                downloadName = `${yr}_${daerah}_${varCount}_Variabel.xlsx`;
            }
            if (!downloadName.endsWith('.xlsx')) downloadName += '.xlsx';

            res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
            res.setHeader('Content-Disposition', `attachment; filename="${downloadName}"`);

            await wb.xlsx.write(res);
            res.end();
        });
    } catch (err) {
        console.error('Export error:', err);
        return res.status(500).json({ success: false, error: err.message });
    }
});

// 4. API: Get template columns
app.get('/api/template-columns', (req, res) => {
    return res.json({ success: true, columns: templateColumns });
});

app.listen(PORT, () => {
    console.log(`[BPS Data Parser Web] Server running at http://localhost:${PORT}`);
});
