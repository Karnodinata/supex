import fs from 'fs';
import { PDFParse } from 'pdf-parse';

async function scan() {
    const dataBuffer = fs.readFileSync('sample_test.pdf');
    const uint8 = new Uint8Array(dataBuffer);
    const parser = new PDFParse(uint8);
    await parser.load();
    const result = await parser.getText();

    console.log(`Loaded ${result.pages.length} pages.`);

    for (const p of result.pages) {
        const lines = p.text.split('\n').map(l => l.trim()).filter(Boolean);
        for (let i = 0; i < Math.min(10, lines.length); i++) {
            const line = lines[i];
            if (/(lanjutan|continued)/i.test(line)) {
                console.log(`[P.${p.num}] CONTINUED LINE: "${line}"`);
                if (lines[i + 1]) console.log(`   Next line: "${lines[i + 1]}"`);
            }
            if (/^(tabel|table)/i.test(line)) {
                console.log(`[P.${p.num}] TABLE LINE: "${line}"`);
                if (lines[i + 1]) console.log(`   Line +1: "${lines[i + 1]}"`);
                if (lines[i + 2]) console.log(`   Line +2: "${lines[i + 2]}"`);
            }
        }
    }
    await parser.destroy();
}

scan().catch(console.error);

