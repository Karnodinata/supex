import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runTest() {
    const baseUrl = 'http://localhost:3000';
    console.log('[*] Testing /api/template-columns...');
    const tColRes = await fetch(`${baseUrl}/api/template-columns`);
    const tColData = await tColRes.json();
    console.log(`[OK] Template columns count: ${tColData.columns.length}`);

    console.log('[*] Testing /api/upload-and-scan with sample_test.pdf...');
    const pdfPath = path.join(process.cwd(), 'sample_test.pdf');
    const fileBytes = fs.readFileSync(pdfPath);
    const blob = new Blob([fileBytes], { type: 'application/pdf' });
    const formData = new FormData();
    formData.append('pdfFile', blob, 'sample_test.pdf');

    const scanRes = await fetch(`${baseUrl}/api/upload-and-scan`, {
        method: 'POST',
        body: formData
    });
    const scanData = await scanRes.json();
    console.log(`[OK] Scan success: ${scanData.success}, Total tables found: ${scanData.totalTables}`);
    console.log('    Metadata:', scanData.metadata);

    const firstTable = scanData.tables[0];
    console.log(`[*] Testing /api/preview-table for Hal. ${firstTable.pageNumber} (${firstTable.tableNumber})...`);
    const prevRes = await fetch(`${baseUrl}/api/preview-table`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            fileId: scanData.fileId,
            pageNumber: firstTable.pageNumber
        })
    });
    const prevData = await prevRes.json();
    console.log(`[OK] Preview success: ${prevData.success}`);
    console.log(`    Headers (${prevData.table.totalCols}):`, prevData.table.headers);
    console.log(`    Rows count: ${prevData.table.totalRows}`);
    if (prevData.table.rows.length > 0) {
        console.log(`    Sample row 0:`, prevData.table.rows[0]);
    }

    console.log('[*] Testing /api/export-excel for Hal. 19 & 20...');
    const exportRes = await fetch(`${baseUrl}/api/export-excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            fileId: scanData.fileId,
            selectedPages: [19, 20],
            selectedTitles: ['Letak Geografis', 'Topografi Wilayah'],
            metadata: scanData.metadata,
            customFilename: 'Test_Hasil_Export.xlsx'
        })
    });
    const arrayBuffer = await exportRes.arrayBuffer();
    const outBuffer = Buffer.from(arrayBuffer);
    fs.writeFileSync('test_output.xlsx', outBuffer);
    console.log(`[OK] Export success! Saved 'test_output.xlsx', size: ${outBuffer.length} bytes`);
}

runTest().catch(err => {
    console.error('[!] Test failed:', err);
    process.exit(1);
});

