import fs from 'fs';
import path from 'path';

async function run() {
    const baseUrl = 'http://localhost:3000';
    console.log('[*] Testing /api/upload-and-scan...');
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
    console.log(`[OK] Scan success: ${scanData.success}, Total tables: ${scanData.totalTables}`);

    // Check Table on Page 43 (Tabel 3.5)
    const tbl35 = scanData.tables.find(t => t.tableNumber === '3.5' || t.pageNumber === 43);
    console.log('[*] Table 3.5:', tbl35);

    if (tbl35) {
        const prev35 = await fetch(`${baseUrl}/api/preview-table`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileId: scanData.fileId, tableId: tbl35.id, pages: tbl35.pages })
        });
        const d35 = await prev35.json();
        console.log('[*] Preview 3.5 raw response:', d35);
    }
}

run().catch(console.error);

