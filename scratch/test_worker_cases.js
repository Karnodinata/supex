import { execFile } from 'child_process';

const specs = {
    tbl_page43: [43],
    tbl_page26: [26],
    tbl_multi_horti: [61, 62]
};

execFile('python', ['-u', 'extract_worker.py', 'sample_test.pdf', JSON.stringify(specs)], (err, stdout, stderr) => {
    if (err) {
        console.error('Error:', err, stderr);
        return;
    }
    const data = JSON.parse(stdout);
    console.log('Success:', data.success);
    
    // Check Page 43 (previously 0 tables)
    console.log('\n--- TBL PAGE 43 (Previously failed to load) ---');
    const t43 = data.results.tbl_page43;
    if (t43) {
        console.log(`Headers (${t43.totalCols}):`, t43.headers);
        console.log(`Total rows: ${t43.totalRows}`);
        console.log('Sample row 0:', t43.rows[0]);
    } else {
        console.log('Failed to load page 43');
    }

    // Check Page 26 (2-tier headers)
    console.log('\n--- TBL PAGE 26 (2-tier headers) ---');
    const t26 = data.results.tbl_page26;
    if (t26) {
        console.log(`Headers (${t26.totalCols}):`, t26.headers);
        console.log(`Total rows: ${t26.totalRows}`);
        console.log('Sample row 0:', t26.rows[0]);
    }

    // Check Multi-page merged table [61, 62]
    console.log('\n--- TBL MULTI HORTI (Merged 61 + 62) ---');
    const tHorti = data.results.tbl_multi_horti;
    if (tHorti) {
        console.log(`Headers (${tHorti.totalCols}):`, tHorti.headers);
        console.log(`Total rows (Pages ${tHorti.pagesIncluded}): ${tHorti.totalRows}`);
        console.log('Row 0 (From Page 61):', tHorti.rows[0]);
        console.log('Row last (From Page 62):', tHorti.rows[tHorti.rows.length - 1]);
    }
});

