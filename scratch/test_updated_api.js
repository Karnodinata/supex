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
    console.log('[*] Table 3.5 (Page 43 borderless):', tbl35 ? `Found! Title: "${tbl35.title}" Hal: ${tbl35.pageNumber}` : 'NOT FOUND');

    if (tbl35) {
        const prev35 = await fetch(`${baseUrl}/api/preview-table`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileId: scanData.fileId, tableId: tbl35.id, pages: tbl35.pages })
        });
        const d35 = await prev35.json();
        console.log(`[OK] Preview 3.5 success: ${d35.success}, Rows: ${d35.table.totalRows}`);
        console.log('    Headers:', d35.table.headers);
        console.log('    Sample row 0:', d35.table.rows[0]);
    }

    // Check Table on Page 26 (Tabel 1.8 - 2-tier headers)
    const tbl18 = scanData.tables.find(t => t.tableNumber === '1.8');
    if (tbl18) {
        console.log(`\n[*] Previewing Table 1.8 (Page 26 - 2 tier headers)...`);
        const prev18 = await fetch(`${baseUrl}/api/preview-table`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileId: scanData.fileId, tableId: tbl18.id, pages: tbl18.pages })
        });
        const d18 = await prev18.json();
        console.log(`[OK] Table 1.8 headers (${d18.table.totalCols}):`);
        d18.table.headers.forEach((h, idx) => console.log(`    Col ${idx}: ${h}`));
        console.log(`    Sample row 0:`, d18.table.rows[0]);
    }

    // Test Export with multi-page table
    console.log('\n[*] Testing /api/export-excel with selectedTables (including multi-page)...');
    const selectedTables = [
        tbl35,
        tbl18,
        { id: 'tbl_horti_simulated', tableNumber: '5.1', title: 'Pertanian & Hortikultura', pages: [61, 62] }
    ].filter(Boolean);

    const expRes = await fetch(`${baseUrl}/api/export-excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            fileId: scanData.fileId,
            selectedTables,
            metadata: scanData.metadata,
            customFilename: '2019_Arongan_Lambalek_Lanjutan_Fixed.xlsx'
        })
    });
    const buf = Buffer.from(await expRes.arrayBuffer());
    fs.writeFileSync('test_export_fixed.xlsx', buf);
    console.log(`[OK] Export successful! Saved 'test_export_fixed.xlsx', size: ${buf.length} bytes`);
}

run().catch(console.error);

