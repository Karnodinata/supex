<!DOCTYPE html><html lang="id"><head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BPS Statistical Multi-Table Selector &amp; Exporter</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Google Fonts: Courier Prime & Space Mono (Typewriter) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&amp;family=Space+Mono:ital,wght@0,400;0,700;1,400&amp;display=swap" rel="stylesheet">
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    /* Font Typewriter / Monospace */
    body {
      font-family: 'Courier Prime', 'Space Mono', Courier, monospace;
      letter-spacing: -0.01em;
    }

    /* Background: Gradasi Muda Halus Putih - Biru Muda - Ungu Muda dengan elemen visual berbaur */
    .bg-gradient-soft {
      background: 
        radial-gradient(circle at 10% 20%, rgba(186, 230, 253, 0.9) 0%, rgba(224, 231, 255, 0.7) 35%, transparent 70%),
        radial-gradient(circle at 85% 25%, rgba(243, 232, 255, 0.95) 0%, rgba(219, 234, 254, 0.6) 45%, transparent 70%),
        radial-gradient(circle at 50% 80%, rgba(233, 213, 255, 0.8) 0%, rgba(199, 210, 254, 0.7) 40%, transparent 75%),
        linear-gradient(135deg, #e0f2fe 0%, #ede9fe 50%, #fdf4ff 100%);
      background-attachment: fixed;
    }

    /* Vibrant ambient color blur blobs di belakang glass */
    .ambient-blob {
      position: absolute;
      border-radius: 50%;
      filter: blur(70px);
      pointer-events: none;
      z-index: 0;
      opacity: 0.75;
    }

    /* Pure Transparant Glass (Hampir tanpa warna / ultra-sheer, murni backdrop-blur dan border bias cahaya) */
    .pure-glass-card {
      background: rgba(255, 255, 255, 0.08); /* Transparansi tinggi, bukan warna solid */
      backdrop-filter: blur(24px) saturate(160%);
      -webkit-backdrop-filter: blur(24px) saturate(160%);
      border: 1px solid rgba(255, 255, 255, 0.35);
      border-top: 1px solid rgba(255, 255, 255, 0.6);
      box-shadow: 0 10px 32px 0 rgba(31, 38, 135, 0.08),
                  inset 0 1px 1px 0 rgba(255, 255, 255, 0.4);
      border-radius: 24px;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .pure-glass-card:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.5);
      box-shadow: 0 14px 40px 0 rgba(31, 38, 135, 0.12),
                  inset 0 1px 1px 0 rgba(255, 255, 255, 0.6);
    }

    /* Transparant Glass Selector Input */
    .pure-glass-select {
      background: rgba(255, 255, 255, 0.06);
      backdrop-filter: blur(20px) saturate(150%);
      -webkit-backdrop-filter: blur(20px) saturate(150%);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-top: 1px solid rgba(255, 255, 255, 0.5);
      border-radius: 16px;
      box-shadow: 0 4px 12px 0 rgba(31, 38, 135, 0.04),
                  inset 0 1px 1px 0 rgba(255, 255, 255, 0.25);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .pure-glass-select:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(165, 180, 252, 0.6);
      box-shadow: 0 6px 18px 0 rgba(99, 102, 241, 0.1);
    }

    /* Animasi Waterdrop Smooth Bergetar Lembut (Riak Cahaya Kaca) */
    @keyframes glassWaterdrop {
      0% {
        transform: scale(0.995);
        box-shadow: 0 0 0 0 rgba(147, 197, 253, 0.7), inset 0 1px 2px rgba(255, 255, 255, 0.8);
      }
      30% {
        transform: scale(1.008);
        box-shadow: 0 0 0 8px rgba(196, 181, 253, 0.35), inset 0 1px 3px rgba(255, 255, 255, 0.9);
      }
      60% {
        transform: scale(0.998);
        box-shadow: 0 0 0 14px rgba(224, 231, 255, 0.15);
      }
      100% {
        transform: scale(1);
        box-shadow: 0 0 0 4px rgba(147, 197, 253, 0.35);
      }
    }

    .waterdrop-pulse {
      background: rgba(255, 255, 255, 0.15) !important;
      border-color: rgba(147, 197, 253, 0.8) !important;
      animation: glassWaterdrop 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }

    /* Glass Tag Pills (Ultra Sheer) */
    .glass-tag {
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.45);
      border-radius: 9999px;
      color: #1e293b;
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.3);
      transition: all 0.2s ease;
    }

    .glass-tag:hover {
      background: rgba(255, 255, 255, 0.25);
      transform: scale(1.02);
    }

    /* Glass Transparant Buttons */
    .glass-button-primary {
      background: rgba(255, 255, 255, 0.12);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.4);
      border-top: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: 16px;
      color: #0f172a;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12),
                  inset 0 1px 1px rgba(255, 255, 255, 0.5);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .glass-button-primary:hover {
      background: rgba(255, 255, 255, 0.22);
      border-color: rgba(255, 255, 255, 0.65);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(99, 102, 241, 0.18),
                  inset 0 1px 2px rgba(255, 255, 255, 0.7);
    }

    .glass-button-primary:active {
      transform: scale(0.98);
    }

    .glass-button-success {
      background: rgba(167, 243, 208, 0.2);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(110, 231, 183, 0.45);
      border-top: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: 16px;
      color: #064e3b;
      box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1),
                  inset 0 1px 1px rgba(255, 255, 255, 0.5);
      transition: all 0.25s ease;
    }

    .glass-button-success:hover {
      background: rgba(167, 243, 208, 0.32);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.16);
    }
  </style>
</head>
<body class="bg-gradient-soft min-h-[1024px] text-slate-800 antialiased p-6 md:p-10 relative overflow-x-hidden" data-stitch-vh="min-h-[1024px]===min-h-screen">

  <!-- Glowing Colored Ambient Blobs (Terlihat jelas tembus melalui kaca transparant) -->
  <div class="ambient-blob w-[480px] h-[480px] -top-20 -left-20 bg-sky-300"></div>
  <div class="ambient-blob w-[520px] h-[520px] top-40 -right-20 bg-purple-300"></div>
  <div class="ambient-blob w-[450px] h-[450px] bottom-10 left-1/4 bg-blue-200"></div>

  <main class="max-w-6xl mx-auto space-y-6 relative z-10">

    <!-- Header Glass Card (Tanpa warna solid, murni blur & bias kaca) -->
    <header class="pure-glass-card p-8 rounded-3xl">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="space-y-2">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 border border-white/40 text-slate-700 backdrop-blur-md">
            <span class="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></span>
            BPS Statistical System
          </div>
          <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-slate-900">
            BPS Statistical Multi-Table Selector &amp; Exporter
          </h1>
          <p class="text-xs md:text-sm text-slate-600 leading-relaxed max-w-2xl">
            Saring data statistik wilayah bertingkat, pratinjau tabel pivot 2D, dan ekspor ke lembar kerja Excel gabungan.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <div class="pure-glass-card px-4 py-3 rounded-2xl flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-white/30 text-sky-800 flex items-center justify-center border border-white/40">
              <i data-lucide="database" class="w-4 h-4"></i>
            </div>
            <div>
              <p class="text-[11px] text-slate-500 font-medium">Database</p>
              <p class="text-xs font-bold text-slate-800">DuckDB Parquet</p>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Filter Columns: 2 Pure Transparant Glass Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Card 1: Filter Wilayah Administrasi -->
      <section class="pure-glass-card p-6 md:p-7 space-y-5 rounded-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-white/25">
          <div class="flex items-center gap-2">
            <span class="p-1.5 rounded-lg bg-white/25 text-sky-800 border border-white/30">
              <i data-lucide="map-pin" class="w-3.5 h-3.5"></i>
            </span>
            <h2 class="text-xs md:text-sm font-bold text-slate-800">Filter Wilayah Administrasi</h2>
          </div>
          <span class="text-[11px] text-slate-500 font-medium">Hirarki Bertingkat</span>
        </div>

        <!-- 1. Provinsi -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-slate-700 flex items-center justify-between">
            <span>1. Pilih Provinsi (bisa pilih banyak)</span>
            <span class="text-[11px] text-sky-800 font-medium">2 Terpilih</span>
          </label>
          <div class="pure-glass-select p-2.5 min-h-[46px] flex flex-wrap items-center gap-1.5 cursor-pointer waterdrop-trigger group">
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Jawa Timur
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Jawa Tengah
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <input type="text" placeholder="Pilih provinsi..." class="bg-transparent text-xs text-slate-800 placeholder-slate-500 outline-none flex-1 min-w-[120px] px-1 font-mono">
            <div class="ml-auto text-slate-500 group-hover:text-sky-700 transition">
              <i data-lucide="chevron-down" class="w-4 h-4"></i>
            </div>
          </div>
        </div>

        <!-- 2. Kabupaten/Kota -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-slate-700 flex items-center justify-between">
            <span>2. Pilih Kabupaten/Kota (bisa pilih banyak)</span>
            <span class="text-[11px] text-sky-800 font-medium">1 Terpilih</span>
          </label>
          <div class="pure-glass-select p-2.5 min-h-[46px] flex flex-wrap items-center gap-1.5 cursor-pointer waterdrop-trigger group">
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Kab. Malang
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <input type="text" placeholder="Pilih kabupaten/kota..." class="bg-transparent text-xs text-slate-800 placeholder-slate-500 outline-none flex-1 min-w-[140px] px-1 font-mono">
            <div class="ml-auto text-slate-500 group-hover:text-sky-700 transition">
              <i data-lucide="chevron-down" class="w-4 h-4"></i>
            </div>
          </div>
        </div>

        <!-- 3. Kecamatan -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-slate-700 flex items-center justify-between">
            <span>3. Pilih Kecamatan (bisa pilih banyak)</span>
            <span class="text-[11px] text-purple-800 font-medium">2 Terpilih</span>
          </label>
          <div class="pure-glass-select p-2.5 min-h-[46px] flex flex-wrap items-center gap-1.5 cursor-pointer waterdrop-trigger group">
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Kec. Kepanjen
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Kec. Singosari
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <input type="text" placeholder="Pilih kecamatan..." class="bg-transparent text-xs text-slate-800 placeholder-slate-500 outline-none flex-1 min-w-[120px] px-1 font-mono">
            <div class="ml-auto text-slate-500 group-hover:text-sky-700 transition">
              <i data-lucide="chevron-down" class="w-4 h-4"></i>
            </div>
          </div>
        </div>

      </section>

      <!-- Card 2: Filter Periode & Judul Tabel -->
      <section class="pure-glass-card p-6 md:p-7 space-y-5 rounded-2xl">
        <div class="flex items-center justify-between pb-3 border-b border-white/25">
          <div class="flex items-center gap-2">
            <span class="p-1.5 rounded-lg bg-white/25 text-purple-800 border border-white/30">
              <i data-lucide="calendar" class="w-3.5 h-3.5"></i>
            </span>
            <h2 class="text-xs md:text-sm font-bold text-slate-800">Filter Periode &amp; Judul Tabel</h2>
          </div>
          <span class="text-[11px] text-slate-500 font-medium">Parameter Tabel</span>
        </div>

        <!-- 4. Tahun -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-slate-700 flex items-center justify-between">
            <span>4. Pilih Tahun (bisa pilih banyak)</span>
            <span class="text-[11px] text-purple-800 font-medium">2 Periode</span>
          </label>
          <div class="pure-glass-select p-2.5 min-h-[46px] flex flex-wrap items-center gap-1.5 cursor-pointer waterdrop-trigger group">
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              2023
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              2024
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <input type="text" placeholder="Pilih tahun..." class="bg-transparent text-xs text-slate-800 placeholder-slate-500 outline-none flex-1 min-w-[100px] px-1 font-mono">
            <div class="ml-auto text-slate-500 group-hover:text-purple-700 transition">
              <i data-lucide="chevron-down" class="w-4 h-4"></i>
            </div>
          </div>
        </div>

        <!-- 5. Judul Tabel -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-slate-700 flex items-center justify-between">
            <span>5. Pilih Tabel (opsional, kosongkan untuk pilih semua)</span>
            <span class="text-[11px] text-slate-500">Opsional</span>
          </label>
          <div class="pure-glass-select p-2.5 min-h-[46px] flex flex-wrap items-center gap-1.5 cursor-pointer waterdrop-trigger group">
            <span class="glass-tag text-xs font-medium px-3 py-1 flex items-center gap-1.5">
              Luas Wilayah dan Kepadatan Penduduk
              <button class="hover:text-red-500 transition"><i data-lucide="x" class="w-3 h-3"></i></button>
            </span>
            <input type="text" placeholder="Cari judul tabel..." class="bg-transparent text-xs text-slate-800 placeholder-slate-500 outline-none flex-1 min-w-[140px] px-1 font-mono">
            <div class="ml-auto text-slate-500 group-hover:text-purple-700 transition">
              <i data-lucide="chevron-down" class="w-4 h-4"></i>
            </div>
          </div>
        </div>

        <div class="p-3 rounded-xl bg-white/10 border border-white/20 text-xs text-slate-600 flex items-center gap-2 backdrop-blur-md">
          <i data-lucide="sparkles" class="w-4 h-4 text-sky-600 shrink-0"></i>
          <span>Klik atau pilih dropdown untuk melihat animasi waterdrop bergetar smooth.</span>
        </div>

      </section>

    </div>

    <!-- Center Action Trigger Button (Glass Transparant) -->
    <div class="flex justify-center pt-2">
      <button class="glass-button-primary px-8 py-3.5 flex items-center gap-2.5 text-xs md:text-sm font-bold">
        <i data-lucide="table" class="w-4 h-4"></i>
        <span>Tampilkan &amp; Siapkan File Excel</span>
      </button>
    </div>

    <!-- Output & Preview Section -->
    <section class="space-y-4 pt-2">
      
      <!-- Status Notice Card (Pure Glass) -->
      <div class="pure-glass-card p-4 rounded-2xl flex items-center justify-between border-emerald-400/30">
        <div class="flex items-center gap-3 text-emerald-900 text-xs md:text-sm font-semibold">
          <span class="w-7 h-7 rounded-xl bg-emerald-500/20 text-emerald-800 flex items-center justify-center border border-emerald-400/30">
            <i data-lucide="check" class="w-4 h-4"></i>
          </span>
          <span>Ditemukan <strong>4 tabel unik</strong> dari kombinasi filter yang dipilih.</span>
        </div>
        <span class="text-[11px] font-medium text-emerald-900 bg-white/20 px-3 py-1 rounded-full border border-white/30">
          Siap Ekspor
        </span>
      </div>

      <!-- Preview Expandable Card (Pure Glass Rounded) -->
      <div class="pure-glass-card rounded-2xl overflow-hidden">
        
        <!-- Accordion Header -->
        <div class="p-4 md:p-5 bg-white/10 flex items-center justify-between border-b border-white/20">
          <div class="flex items-center gap-3">
            <span class="p-2 rounded-xl bg-white/20 text-sky-800 border border-white/30">
              <i data-lucide="file-text" class="w-4 h-4"></i>
            </span>
            <div>
              <h3 class="text-xs md:text-sm font-bold text-slate-900">
                [KEC. KEPANJEN - 2024] Tabel 1.1: Luas Wilayah dan Kepadatan Penduduk menurut Desa/Kelurahan
              </h3>
              <p class="text-[11px] text-slate-500">Sheet: Kepanjen_2024 • Format Matriks 2D</p>
            </div>
          </div>
          <span class="text-[11px] text-sky-900 font-semibold bg-white/20 px-3 py-1 rounded-full border border-white/30">
            Preview 1 dari 4
          </span>
        </div>

        <!-- 2D Table Content (Transparant Table) -->
        <div class="p-4 md:p-5 overflow-x-auto">
          <table class="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="bg-white/20 text-slate-800 font-bold border-b border-white/30">
                <th class="p-3 rounded-l-xl">Uraian / Wilayah</th>
                <th class="p-3 text-center">Luas (km²)</th>
                <th class="p-3 text-center">Jumlah Penduduk (Jiwa)</th>
                <th class="p-3 text-center">Kepadatan (/km²)</th>
                <th class="p-3 text-center rounded-r-xl">Persentase (%)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/15">
              <tr class="hover:bg-white/15 transition">
                <td class="p-3 font-semibold text-slate-800">1. Kelurahan Kepanjen</td>
                <td class="p-3 text-center">4.25</td>
                <td class="p-3 text-center font-medium">14,820</td>
                <td class="p-3 text-center">3,487</td>
                <td class="p-3 text-center font-semibold text-purple-900">14.2%</td>
              </tr>
              <tr class="hover:bg-white/15 transition">
                <td class="p-3 font-semibold text-slate-800">2. Desa Panggungrejo</td>
                <td class="p-3 text-center">3.80</td>
                <td class="p-3 text-center font-medium">12,150</td>
                <td class="p-3 text-center">3,197</td>
                <td class="p-3 text-center font-semibold text-purple-900">11.6%</td>
              </tr>
              <tr class="hover:bg-white/15 transition">
                <td class="p-3 font-semibold text-slate-800">3. Desa Talangagung</td>
                <td class="p-3 text-center">5.10</td>
                <td class="p-3 text-center font-medium">11,940</td>
                <td class="p-3 text-center">2,341</td>
                <td class="p-3 text-center font-semibold text-purple-900">11.4%</td>
              </tr>
              <tr class="hover:bg-white/15 transition">
                <td class="p-3 font-semibold text-slate-800">4. Desa Sengguruh</td>
                <td class="p-3 text-center">4.92</td>
                <td class="p-3 text-center font-medium">10,210</td>
                <td class="p-3 text-center">2,075</td>
                <td class="p-3 text-center font-semibold text-purple-900">9.8%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-5 py-3 bg-white/10 border-t border-white/20 flex justify-between items-center text-[11px] text-slate-500">
          <span>Menampilkan 4 baris data wilayah</span>
          <span>...dan 3 tabel lainnya telah disusun ke dalam file Excel.</span>
        </div>
      </div>

      <!-- Download Button Card (Pure Glass) -->
      <div class="pure-glass-card p-5 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-800 flex items-center justify-center border border-emerald-400/30">
            <i data-lucide="file-spreadsheet" class="w-5 h-5"></i>
          </div>
          <div>
            <h4 class="font-bold text-slate-800 text-xs md:text-sm">File Excel Siap Diunduh</h4>
            <p class="text-[11px] text-slate-500">Sheet katalog Daftar_Tabel dan sheet individual per kecamatan.</p>
          </div>
        </div>

        <button class="glass-button-success px-6 py-3 flex items-center justify-center gap-2 text-xs md:text-sm font-bold w-full md:w-auto">
          <i data-lucide="download" class="w-4 h-4"></i>
          <span>Download Seluruh Tabel Terpilih (.xlsx)</span>
        </button>
      </div>

    </section>

  </main>

  <script>
    // Inisialisasi Ikon
    lucide.createIcons();

    // Animasi Waterdrop Smooth Bergetar saat Selector Diklik / Fokus
    document.querySelectorAll('.waterdrop-trigger').forEach(trigger => {
      trigger.addEventListener('click', function() {
        this.classList.remove('waterdrop-pulse');
        void this.offsetWidth; // Force Reflow
        this.classList.add('waterdrop-pulse');
      });

      const innerInput = trigger.querySelector('input');
      if (innerInput) {
        innerInput.addEventListener('focus', () => {
          trigger.classList.remove('waterdrop-pulse');
          void trigger.offsetWidth;
          trigger.classList.add('waterdrop-pulse');
        });
      }
    });
  </script>


</body></html>