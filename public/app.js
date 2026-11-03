// BPS Data Parser & Visualizer - Client App
document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    fileId: null,
    metadata: null,
    allTables: [],
    selectedTableIds: new Set(),
    tableMap: new Map(),
    activeSector: 'ALL',
    searchQuery: '',
    activePreviewTableId: null,
    previewCache: new Map(),
    isLoadingPreview: false
  };

  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('pdf-file-input');
  const dropzoneText = document.getElementById('dropzone-text');
  
  const metaBanner = document.getElementById('meta-banner');
  const metaFilename = document.getElementById('meta-filename');
  const metaDaerah = document.getElementById('meta-daerah');
  const metaYear = document.getElementById('meta-year');
  const metaPages = document.getElementById('meta-pages');
  const metaTablesCount = document.getElementById('meta-tables-count');

  const selectionSection = document.getElementById('selection-section');
  const previewSection = document.getElementById('preview-section');
  const exportSection = document.getElementById('export-section');

  const searchInput = document.getElementById('search-tables-input');
  const sectorChips = document.getElementById('sector-chips-container');
  const tableRowsList = document.getElementById('table-rows-list');
  const checkAllHeader = document.getElementById('check-all-header');
  const btnSelectAll = document.getElementById('btn-select-all');
  const btnDeselectAll = document.getElementById('btn-deselect-all');

  const previewTabsContainer = document.getElementById('preview-tabs-container');
  const previewTableContainer = document.getElementById('preview-table-container');
  const previewMetaInfo = document.getElementById('preview-meta-info');

  const exportSelectedBadge = document.getElementById('export-selected-badge');
  const exportFilenameInput = document.getElementById('export-filename-input');
  const btnExportExcel = document.getElementById('btn-export-excel');
  const btnExportText = document.getElementById('btn-export-text');
  const alertContainer = document.getElementById('alert-container');

  // Step Indicators
  const stepCards = [
    document.getElementById('step-card-1'),
    document.getElementById('step-card-2'),
    document.getElementById('step-card-3'),
    document.getElementById('step-card-4')
  ];

  function setStepActive(stepNum) {
    stepCards.forEach((card, idx) => {
      if (idx + 1 < stepNum) {
        card.className = 'step-card completed';
      } else if (idx + 1 === stepNum) {
        card.className = 'step-card active';
      } else {
        card.className = 'step-card';
      }
    });
  }

  function showAlert(msg, type = 'error') {
    alertContainer.style.display = 'block';
    alertContainer.className = `alert alert-${type}`;
    alertContainer.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <span>${escapeHtml(msg)}</span>
    `;
    setTimeout(() => {
      alertContainer.style.display = 'none';
    }, 6000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // File Upload Handlers
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showAlert('Format berkas harus berupa PDF.', 'error');
      return;
    }

    dropzoneText.innerHTML = `
      <span class="spinner" style="border-color: rgba(2,132,199,0.3); border-top-color: #0284C7;"></span>
      Sedang memindai struktur dokumen: <strong>${escapeHtml(file.name)}</strong>...
    `;

    const formData = new FormData();
    formData.append('pdfFile', file);

    try {
      const res = await fetch('/api/upload-and-scan', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || 'Gagal memproses file PDF.');
      }

      state.fileId = data.fileId;
      state.metadata = data.metadata;
      state.allTables = data.tables;
      state.selectedTableIds.clear();
      state.tableMap.clear();
      state.previewCache.clear();

      data.tables.forEach(t => {
        state.tableMap.set(t.id, t);
      });

      // Update UI with metadata
      metaFilename.textContent = data.metadata.filename;
      metaDaerah.textContent = data.metadata.kecamatan !== 'Kecamatan_Umum' 
        ? `Kec. ${data.metadata.kecamatan} (${data.metadata.kabupaten})` 
        : data.metadata.kabupaten;
      metaYear.textContent = data.metadata.year;
      metaPages.textContent = `${data.metadata.totalPages} Halaman`;
      metaTablesCount.textContent = `${data.totalTables} Tabel Statistik`;
      metaBanner.style.display = 'grid';

      dropzoneText.innerHTML = `✓ <strong>${escapeHtml(file.name)}</strong> siap diolah (${data.scanTimeMs}ms)`;

      // Unhide sections
      selectionSection.style.display = 'block';
      previewSection.style.display = 'block';
      exportSection.style.display = 'block';

      // Auto-select first 3 tables for instant preview
      const initialSelection = data.tables.slice(0, 3);
      initialSelection.forEach(t => state.selectedTableIds.add(t.id));

      renderTableList();
      updateFilenamePreview();
      updateSelectionSummary();

      if (initialSelection.length > 0) {
        loadTablePreview(initialSelection[0].id);
      }

      setStepActive(2);
      showAlert(`Berhasil memindai ${data.totalTables} tabel dalam ${data.scanTimeMs}ms!`, 'success');
    } catch (err) {
      console.error(err);
      dropzoneText.textContent = 'Gagal memindai file. Klik atau seret file PDF lain.';
      showAlert(err.message, 'error');
    }
  }

  // Filter & Search Handlers
  searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    renderTableList();
  });

  sectorChips.addEventListener('click', (e) => {
    const btn = e.target.closest('.chip-btn');
    if (!btn) return;
    document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.activeSector = btn.getAttribute('data-sector');
    renderTableList();
  });

  // Table List Rendering
  function renderTableList() {
    const filtered = state.allTables.filter(t => {
      const matchSector = state.activeSector === 'ALL' || t.sector === state.activeSector;
      const matchQuery = !state.searchQuery || 
        t.title.toLowerCase().includes(state.searchQuery) ||
        t.tableNumber.toLowerCase().includes(state.searchQuery) ||
        t.sector.toLowerCase().includes(state.searchQuery);
      return matchSector && matchQuery;
    });

    if (filtered.length === 0) {
      tableRowsList.innerHTML = `<div class="empty-state">Tidak ada tabel yang cocok dengan filter "${escapeHtml(state.searchQuery)}".</div>`;
      return;
    }

    tableRowsList.innerHTML = filtered.map(t => {
      const isChecked = state.selectedTableIds.has(t.id);
      const cleanSectorName = t.sector.replace(/^[0-9]+_/, '').replace(/_/g, ' ');

      const pageStr = t.pages && t.pages.length > 1 
        ? `${t.pages[0]}-${t.pages[t.pages.length - 1]}`
        : `${t.pageNumber}`;

      const contBadge = t.isContinued 
        ? `<span class="cont-tag" title="Tabel bersambung ${t.pageCount} halaman">${t.pageCount} Hal</span>` 
        : '';

      return `
        <div class="table-row-item ${isChecked ? 'selected' : ''}" data-id="${t.id}">
          <span><input type="checkbox" class="table-check" data-id="${t.id}" ${isChecked ? 'checked' : ''}></span>
          <span style="font-weight: 700;">${escapeHtml(t.tableNumber || '-')}</span>
          <span title="${escapeHtml(t.title)}">${escapeHtml(t.title)} ${contBadge}</span>
          <span><span class="sector-tag">${escapeHtml(cleanSectorName)}</span></span>
          <span style="color: var(--text-muted); font-size: 12px;">Hal. ${pageStr}</span>
          <span>
            <button type="button" class="btn-secondary btn-preview-single" data-id="${t.id}" style="padding: 2px 8px; font-size: 11px;">
              Preview
            </button>
          </span>
        </div>
      `;
    }).join('');

    // Attach row events
    tableRowsList.querySelectorAll('.table-check').forEach(chk => {
      chk.addEventListener('change', (e) => {
        const id = e.target.getAttribute('data-id');
        if (e.target.checked) {
          state.selectedTableIds.add(id);
          loadTablePreview(id);
        } else {
          state.selectedTableIds.delete(id);
        }
        updateSelectionSummary();
        updateFilenamePreview();
        renderPreviewTabs();
      });
    });

    tableRowsList.querySelectorAll('.btn-preview-single').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        state.selectedTableIds.add(id);
        renderTableList();
        updateSelectionSummary();
        updateFilenamePreview();
        loadTablePreview(id);
        setStepActive(3);
      });
    });

    tableRowsList.querySelectorAll('.table-row-item').forEach(row => {
      row.addEventListener('click', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') return;
        const id = row.getAttribute('data-id');
        loadTablePreview(id);
        setStepActive(3);
      });
    });
  }

  // Select / Deselect All
  btnSelectAll.addEventListener('click', () => {
    state.allTables.forEach(t => state.selectedTableIds.add(t.id));
    renderTableList();
    updateSelectionSummary();
    updateFilenamePreview();
    renderPreviewTabs();
    if (state.selectedTableIds.size > 0 && !state.activePreviewTableId) {
      loadTablePreview(Array.from(state.selectedTableIds)[0]);
    }
  });

  btnDeselectAll.addEventListener('click', () => {
    state.selectedTableIds.clear();
    renderTableList();
    updateSelectionSummary();
    updateFilenamePreview();
    renderPreviewTabs();
  });

  checkAllHeader.addEventListener('change', (e) => {
    if (e.target.checked) {
      state.allTables.forEach(t => state.selectedTableIds.add(t.id));
    } else {
      state.selectedTableIds.clear();
    }
    renderTableList();
    updateSelectionSummary();
    updateFilenamePreview();
    renderPreviewTabs();
  });

  function updateSelectionSummary() {
    const count = state.selectedTableIds.size;
    exportSelectedBadge.textContent = `${count} Tabel Dipilih`;
    btnExportExcel.disabled = count === 0;

    checkAllHeader.checked = count === state.allTables.length && count > 0;
  }

  function updateFilenamePreview() {
    if (!state.metadata) return;
    const yr = state.metadata.year || '2024';
    const daerah = (state.metadata.kecamatan !== 'Kecamatan_Umum' ? state.metadata.kecamatan : state.metadata.kabupaten)
      .replace(/[^A-Za-z0-9]/g, '_');
    
    let varSummary = 'Semua_Variabel';
    if (state.selectedTableIds.size === 1) {
      const id = Array.from(state.selectedTableIds)[0];
      const t = state.tableMap.get(id);
      const title = t ? t.title : 'Tabel';
      varSummary = title.split(' ').slice(0, 3).join('_').replace(/[^A-Za-z0-9_]/g, '');
    } else if (state.selectedTableIds.size > 1) {
      varSummary = `${state.selectedTableIds.size}_Variabel`;
    }

    exportFilenameInput.value = `${yr}_${daerah}_${varSummary}.xlsx`;
  }

  // Preview Functions
  async function loadTablePreview(tableId) {
    const t = state.tableMap.get(tableId);
    if (!t) return;

    state.activePreviewTableId = tableId;
    renderPreviewTabs();

    const title = t.title || `Tabel ${t.tableNumber}`;
    const pageLabel = t.pages && t.pages.length > 1 
      ? `Hal. ${t.pages[0]} - ${t.pages[t.pages.length - 1]} (${t.pages.length} Halaman Tergabung)`
      : `Hal. ${t.pageNumber}`;

    previewMetaInfo.textContent = `Memuat ${title} (${pageLabel})...`;

    if (state.previewCache.has(tableId)) {
      renderPreviewGrid(state.previewCache.get(tableId), t);
      return;
    }

    previewTableContainer.innerHTML = `
      <div class="empty-state">
        <span class="spinner" style="border-color: rgba(2,132,199,0.3); border-top-color: #0284C7;"></span>
        Mengekstrak data ${escapeHtml(title)} (${escapeHtml(pageLabel)})...
      </div>
    `;

    try {
      const res = await fetch('/api/preview-table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fileId: state.fileId, 
          tableId: t.id, 
          pageNumber: t.pageNumber,
          pages: t.pages 
        })
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || 'Gagal memuat pratinjau tabel.');
      }

      state.previewCache.set(tableId, data.table);
      renderPreviewGrid(data.table, t);
    } catch (err) {
      previewTableContainer.innerHTML = `<div class="empty-state" style="color: var(--danger);">Gagal ekstraksi tabel: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderPreviewTabs() {
    const selectedArr = Array.from(state.selectedTableIds);
    if (selectedArr.length === 0) {
      previewTabsContainer.innerHTML = '';
      return;
    }

    previewTabsContainer.innerHTML = selectedArr.map(id => {
      const isActive = id === state.activePreviewTableId;
      const t = state.tableMap.get(id);
      const label = t ? (t.tableNumber ? `Tabel ${t.tableNumber}` : `Hal.${t.pageNumber}`) : id;
      const contMarker = t && t.isContinued ? ' ↳' : '';
      return `
        <button type="button" class="tab-btn ${isActive ? 'active' : ''}" data-id="${id}">
          ${escapeHtml(label)}${contMarker}
        </button>
      `;
    }).join('');

    previewTabsContainer.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-id');
        loadTablePreview(id);
      });
    });
  }

  function renderPreviewGrid(tableData, tableObj) {
    const pageLabel = tableData.pagesIncluded && tableData.pagesIncluded.length > 1
      ? `Hal. ${tableData.pagesIncluded[0]}-${tableData.pagesIncluded[tableData.pagesIncluded.length - 1]} (${tableData.pagesIncluded.length} Halaman Tergabung)`
      : `Hal. ${tableObj.pageNumber}`;

    previewMetaInfo.textContent = `[${tableObj.tableNumber ? 'Tabel ' + tableObj.tableNumber : 'Tabel'}] ${tableData.totalRows} Baris × ${tableData.totalCols} Kolom (${pageLabel})`;

    if (!tableData.headers || tableData.headers.length === 0) {
      previewTableContainer.innerHTML = `<div class="empty-state">Tabel tidak memiliki kolom yang terdeteksi.</div>`;
      return;
    }

    const headerHtml = `
      <thead>
        <tr>
          <th style="width: 40px; text-align: center;">#</th>
          ${tableData.headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}
        </tr>
      </thead>
    `;

    const bodyHtml = `
      <tbody>
        ${tableData.rows.map((r, rIdx) => {
          return `
            <tr>
              <td style="text-align: center; color: var(--text-muted); font-size: 11px;">${rIdx + 1}</td>
              ${r.map((cell, cIdx) => {
                const isNum = cIdx > 0 && /^-?\d+([.,]\d+)?$/.test(String(cell || '').trim());
                return `<td class="${isNum ? 'cell-number' : ''}">${escapeHtml(cell || '-')}</td>`;
              }).join('')}
            </tr>
          `;
        }).join('')}
      </tbody>
    `;

    previewTableContainer.innerHTML = `
      <table class="preview-data-table">
        ${headerHtml}
        ${bodyHtml}
      </table>
    `;
  }

  // Export Excel Handler
  btnExportExcel.addEventListener('click', async () => {
    if (state.selectedTableIds.size === 0) {
      showAlert('Pilih minimal satu tabel sebelum mengekspor.', 'error');
      return;
    }

    const selectedTables = Array.from(state.selectedTableIds).map(id => state.tableMap.get(id)).filter(Boolean);
    const customFilename = exportFilenameInput.value.trim() || 'Hasil_Export_BPS.xlsx';

    btnExportExcel.disabled = true;
    btnExportText.innerHTML = `<span class="spinner"></span> Membuat file Excel...`;

    try {
      const res = await fetch('/api/export-excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileId: state.fileId,
          selectedTables,
          metadata: state.metadata,
          customFilename
        })
      });

      if (!res.ok) {
        const errorJson = await res.json();
        throw new Error(errorJson.error || 'Gagal mengunduh Excel.');
      }

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = customFilename.endsWith('.xlsx') ? customFilename : `${customFilename}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setStepActive(4);
      showAlert(`Berkas "${customFilename}" berhasil diexport dan diunduh!`, 'success');
    } catch (err) {
      showAlert(err.message, 'error');
    } finally {
      btnExportExcel.disabled = false;
      btnExportText.textContent = 'Export ke Excel (.xlsx)';
    }
  });
});
