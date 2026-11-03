import fs from 'fs';
import { PDFParse } from 'pdf-parse';

const SECTORS_MAP = {
    '1': '1_Geografi_Iklim',
    '2': '2_Pemerintahan',
    '3': '3_Penduduk',
    '4': '4_Sosial',
    '5': '5_Pertanian',
    '6': '6_Energi_Perdagangan',
    '7': '7_Transportasi_Lainnya'
};

async function testScan() {
    const dataBuffer = fs.readFileSync('sample_test.pdf');
    const uint8 = new Uint8Array(dataBuffer);
    const parser = new PDFParse(uint8);
    await parser.load();
    const result = await parser.getText();
    const pages = result.pages || [];

    const tables = [];

    for (const p of pages) {
        const lines = p.text.split('\n').map(l => l.trim()).filter(Boolean);
        // Only skip if DAFTAR ISI / DAFTAR TABEL is strictly in the top 3 lines
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

                // Clean title from "Lanjutan" / "Continued" tags
                title = title.replace(/\(?\s*(?:Lanjutan|Continued)\s*\)?/gi, '').trim();

                if (!title || title.length < 5) {
                    const titleLines = [];
                    for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
                        const nxt = lines[j];
                        if (/^(Table|Tabel|Sumber|Source|\(\d+\)|[A-Z\s]{5,}$)/i.test(nxt)) break;
                        if (nxt.startsWith('Nama ') || nxt.startsWith('Desa ') || nxt.startsWith('http')) break;
                        titleLines.push(nxt);
                    }
                    title = (title + ' ' + titleLines.join(' ')).trim();
                }

                if (!title) title = 'Tabel Statistik';

                const secNum = tableNum ? tableNum.split('.')[0] : '1';
                const sector = SECTORS_MAP[secNum] || 'Umum';

                // Check existing table
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
                        pageCount: 1
                    });
                }
                break;
            }
        }
    }

    console.log(`Total unique tables found: ${tables.length}`);
    const continued = tables.filter(t => t.isContinued);
    console.log(`Tables with multiple pages (continued): ${continued.length}`);
    continued.forEach(t => {
        console.log(`  - Tabel ${t.tableNumber}: ${t.title} (Pages: ${t.pages.join(', ')})`);
    });

    console.log('\nSample 10 tables:');
    tables.slice(0, 10).forEach(t => {
        console.log(`  [Tabel ${t.tableNumber}] ${t.title} | Hal: ${t.pages.join('-')}`);
    });

    await parser.destroy();
}

testScan().catch(console.error);

