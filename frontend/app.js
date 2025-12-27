// Global state
let currentVoters = [];

// Upload Single PDF
async function uploadPDF() {
    await processFileOrFolder('pdf');
}

// Batch Process Folder
async function batchProcess() {
    await processFileOrFolder('batch');
}

// Generic Process Handler
async function processFileOrFolder(mode) {
    try {
        // Enforce template selection before processing
        const selectEl = document.getElementById('templateSelect');
        const templateKey = selectEl ? selectEl.value : '';
        if (!templateKey) {
            alert('Please select a template before processing.');
            return;
        }
        // Inform backend about selected template
        try {
            await pywebview.api.set_template(templateKey);
        } catch (e) {
            console.warn('Could not set template on backend:', e);
        }

        // Get page range (optional)
        const startPageInput = document.getElementById('startPage');
        const endPageInput = document.getElementById('endPage');
        const startPage = startPageInput && startPageInput.value ? parseInt(startPageInput.value) : null;
        const endPage = endPageInput && endPageInput.value ? parseInt(endPageInput.value) : null;

        let result;
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('uploadBtn').disabled = true;
        document.getElementById('batchBtn').disabled = true;
        
        // Reset progress display
        document.getElementById('currentPage').textContent = '0';
        document.getElementById('totalPages').textContent = '0';
        document.getElementById('votersFound').textContent = '0';
        document.getElementById('logContent').innerHTML = 'Starting...';
        document.getElementById('progressFill').style.width = '0%';
        
        // Start progress polling
        let progressInterval = setInterval(async () => {
            try {
                const progress = await pywebview.api.get_progress();
                if (progress && progress.status) {
                    const status = progress.status;
                    document.getElementById('currentPage').textContent = status.current_page || 0;
                    document.getElementById('totalPages').textContent = status.total_pages || 0;
                    document.getElementById('votersFound').textContent = status.voters_found || 0;
                    
                    // Update progress bar
                    if (status.total_pages > 0) {
                        const pct = Math.round((status.current_page / status.total_pages) * 100);
                        document.getElementById('progressFill').style.width = pct + '%';
                        document.getElementById('progressText').textContent = `Processing page ${status.current_page} of ${status.total_pages}...`;
                    }
                }
                if (progress && progress.messages && progress.messages.length > 0) {
                    const logHtml = progress.messages.map(msg => `<div>${msg}</div>`).join('');
                    const logEl = document.getElementById('logContent');
                    logEl.innerHTML = logHtml;
                    logEl.scrollTop = logEl.scrollHeight;
                }
            } catch (e) {
                console.log('Progress poll error:', e);
            }
        }, 500);

        if (mode === 'pdf') {
            const filePath = await pywebview.api.select_pdf();
            if (!filePath) { 
                resetUI(); return; 
            }
            const pageRangeInfo = (startPage || endPage) ? ` (pages ${startPage || 1}-${endPage || 'end'})` : '';
            document.getElementById('fileInfo').textContent = `Processing: ${filePath.split('\\').pop()}${pageRangeInfo}`;
            result = await pywebview.api.process_pdf(filePath, startPage, endPage);
        } else {
            const folderPath = await pywebview.api.select_folder();
            if (!folderPath) { 
                resetUI(); return; 
            }
            document.getElementById('fileInfo').textContent = `Batch Processing: ${folderPath}`;
            result = await pywebview.api.process_batch(folderPath);
        }

        if (result.success) {
            currentVoters = result.voters;
            displayResults(result);
            
            // Different messages for single PDF vs batch
            if (mode === 'batch') {
                const filesDetail = result.files_detail || [];
                const processedCount = result.processed_files || filesDetail.length;
                const failedCount = result.failed_files || 0;
                
                let message = `✅ Batch Processing Complete!\n\n`;
                message += `📊 Summary:\n`;
                message += `• Total PDFs: ${result.total_files}\n`;
                message += `• Successfully processed: ${processedCount}\n`;
                message += `• Failed: ${failedCount}\n`;
                message += `• Total voters extracted: ${result.total_voters}\n\n`;
                
                if (filesDetail.length > 0) {
                    message += `📁 Excel files created in the same folder:\n`;
                    filesDetail.slice(0, 5).forEach(f => {
                        message += `  • ${f.excel} (${f.voters} voters)\n`;
                    });
                    if (filesDetail.length > 5) {
                        message += `  ... and ${filesDetail.length - 5} more files\n`;
                    }
                }
                
                alert(message);
            } else {
                alert(`✅ Processing Complete!\nFound ${result.total_voters} voters.`);
            }
        } else {
            alert(`❌ Error: ${result.error}`);
        }
        
        // Stop progress polling
        clearInterval(progressInterval);
        try { await pywebview.api.clear_progress(); } catch (e) {}
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error}`);
    } finally {
        resetUI();
    }
}

function resetUI() {
    document.getElementById('uploadBtn').disabled = false;
    document.getElementById('batchBtn').disabled = false;
    document.getElementById('progressSection').style.display = 'none';
}

// Display results
function displayResults(result) {
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('totalCount').textContent = `${result.total_voters} voters`;
    
    // Populate page filter dropdown
    populatePageFilter();
    
    // Update statistics
    updateStats();
    
    // Render the table
    renderTable();
}

// Render Table
function renderTable() {
    const tbody = document.getElementById('votersTableBody');
    tbody.innerHTML = '';
    
    currentVoters.forEach((voter, index) => {
        const row = document.createElement('tr');
        
        // Validation checks
        const hasEpicError = !voter.epic || voter.epic === 'ERROR_MISSING_EPIC';
        const hasMissingName = !voter.name_marathi && !voter.name_english;
        const hasInvalidAge = voter.age && (parseInt(voter.age) < 18 || parseInt(voter.age) > 120);
        
        // Apply row styling based on validation
        if (hasEpicError) {
            row.style.background = 'rgba(239, 68, 68, 0.15)';
            row.style.borderLeft = '3px solid #ef4444';
        } else if (hasMissingName) {
            row.style.background = 'rgba(245, 158, 11, 0.15)';
            row.style.borderLeft = '3px solid #f59e0b';
        }
        
        // Format EPIC with error badge
        const epicDisplay = hasEpicError 
            ? `<span style="color: #ef4444;">⚠️ ${voter.epic || 'Missing'}</span>` 
            : voter.epic;
        
        // Format name with warning if missing
        const nameMarathiDisplay = hasMissingName 
            ? `<span style="color: #f59e0b;">⚠️ Missing</span>` 
            : (voter.name_marathi || '');
        
        // Format age with warning if invalid
        const ageDisplay = hasInvalidAge 
            ? `<span style="color: #f59e0b;" title="Age seems invalid">${voter.age} ⚠️</span>` 
            : (voter.age || '');
        
        row.innerHTML = `
            <td>${voter.page_number || ''}</td>
            <td>${voter.part_no || '-'}</td>
            <td>${epicDisplay}</td>
            <td>${nameMarathiDisplay}</td>
            <td>${voter.name_english || ''}</td>
            <td>${voter.relation_type || ''}</td>
            <td>${voter.relation_name_english || ''}</td>
            <td>${ageDisplay}</td>
            <td>${voter.gender || ''}</td>
            <td>
                <button onclick="editRecord(${index})" style="background:none; border:none; cursor:pointer;" title="Edit">✏️</button>
                <button onclick="deleteRecord(${index})" style="background:none; border:none; cursor:pointer;" title="Delete">🗑️</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    document.getElementById('totalCount').textContent = `${currentVoters.length} voters`;
    
    // Update statistics
    updateStats();
}

// Delete Record
function deleteRecord(index) {
    if (confirm('Are you sure you want to delete this record?')) {
        currentVoters.splice(index, 1);
        renderTable();
    }
}

// Clear All Records
function clearAllRecords() {
    if (currentVoters.length === 0) {
        alert('No records to clear.');
        return;
    }
    
    if (confirm(`Are you sure you want to delete all ${currentVoters.length} records?\n\nThis action cannot be undone.`)) {
        currentVoters = [];
        renderTable();
        document.getElementById('resultsSection').style.display = 'none';
        alert('✅ All records cleared successfully!');
    }
}

// Edit/Add Modal Logic
let isEditing = false;
let editIndex = -1;

function openAddModal() {
    isEditing = false;
    editIndex = -1;
    document.getElementById('modalTitle').textContent = 'Add New Record';
    document.getElementById('editForm').reset();
    document.getElementById('editModal').style.display = 'flex';
}

function editRecord(index) {
    isEditing = true;
    editIndex = index;
    const v = currentVoters[index];
    
    document.getElementById('modalTitle').textContent = 'Edit Record';
    document.getElementById('editEpic').value = v.epic || '';
    document.getElementById('editPartNo').value = v.part_no || '';
    document.getElementById('editNameMar').value = v.name_marathi || '';
    document.getElementById('editNameEng').value = v.name_english || '';
    document.getElementById('editRelType').value = v.relation_type || 'Father';
    document.getElementById('editRelName').value = v.relation_name_english || '';
    document.getElementById('editAge').value = v.age || '';
    document.getElementById('editGender').value = v.gender || 'Male';
    
    document.getElementById('editModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

function saveRecord(event) {
    event.preventDefault();
    
    const newRecord = {
        epic: document.getElementById('editEpic').value,
        part_no: document.getElementById('editPartNo').value,
        name_marathi: document.getElementById('editNameMar').value,
        name_english: document.getElementById('editNameEng').value,
        relation_type: document.getElementById('editRelType').value,
        relation_name_english: document.getElementById('editRelName').value,
        age: document.getElementById('editAge').value,
        gender: document.getElementById('editGender').value,
        page_number: isEditing ? currentVoters[editIndex].page_number : 'Manual',
        serial_no: isEditing ? currentVoters[editIndex].serial_no : ''
    };
    
    // Auto-transliterate Relation Name if missing (simple fallback)
    if (!newRecord.relation_name_marathi && isEditing) {
        newRecord.relation_name_marathi = currentVoters[editIndex].relation_name_marathi; // Keep existing
    }

    if (isEditing) {
        // Merge with existing to keep other fields
        currentVoters[editIndex] = { ...currentVoters[editIndex], ...newRecord };
    } else {
        currentVoters.push(newRecord);
    }
    
    closeModal();
    renderTable();
}

// Export to Excel
async function exportExcel() {
    try {
        if (currentVoters.length === 0) {
            alert('No data to export!');
            return;
        }
        
        // Push updates to backend before export? 
        // No, we can just send the currentVoters list back to Python!
        // Wait, pywebview API is one-way usually? No, we can pass args.
        // But `excel_export` is checking `self.current_data` in Python.
        // We need to UPDATE Python's state with our edited data.
        
        // Let's add an API method: update_data(data)
        await pywebview.api.update_data(currentVoters);
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const defaultPath = `voter_data_${timestamp}.xlsx`;
        
        const result = await pywebview.api.export_to_excel(defaultPath);
        
        if (result.success) {
            alert(`✅ Exported ${result.count} voters to:\n${result.path}`);
        } else {
            alert(`❌ Export failed: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Export error:', error);
        alert(`Error: ${error}`);
    }
}

// ============================================
// SEARCH, FILTER & STATISTICS FUNCTIONS
// ============================================

// Filter table based on search and filter inputs
function filterTable() {
    const searchTerm = (document.getElementById('searchInput').value || '').toLowerCase();
    const genderFilter = document.getElementById('genderFilter').value;
    const pageFilter = document.getElementById('pageFilter').value;
    
    const tbody = document.getElementById('votersTableBody');
    tbody.innerHTML = '';
    
    let filteredCount = 0;
    
    currentVoters.forEach((voter, index) => {
        // Apply search filter
        const searchMatch = !searchTerm || 
            (voter.epic || '').toLowerCase().includes(searchTerm) ||
            (voter.name_marathi || '').toLowerCase().includes(searchTerm) ||
            (voter.name_english || '').toLowerCase().includes(searchTerm) ||
            (voter.relation_name_english || '').toLowerCase().includes(searchTerm) ||
            (voter.relation_name_marathi || '').toLowerCase().includes(searchTerm);
        
        // Apply gender filter
        const genderMatch = !genderFilter || voter.gender === genderFilter;
        
        // Apply page filter
        const pageMatch = !pageFilter || String(voter.page_number) === pageFilter;
        
        if (searchMatch && genderMatch && pageMatch) {
            filteredCount++;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${voter.page_number || ''}</td>
                <td>${voter.part_no || '-'}</td>
                <td>${voter.epic || ''}</td>
                <td>${voter.name_marathi || ''}</td>
                <td>${voter.name_english || ''}</td>
                <td>${voter.relation_type || ''}</td>
                <td>${voter.relation_name_english || ''}</td>
                <td>${voter.age || ''}</td>
                <td>${voter.gender || ''}</td>
                <td>
                    <button onclick="editRecord(${index})" style="background:none; border:none; cursor:pointer;" title="Edit">✏️</button>
                    <button onclick="deleteRecord(${index})" style="background:none; border:none; cursor:pointer;" title="Delete">🗑️</button>
                </td>
            `;
            tbody.appendChild(row);
        }
    });
    
    // Update filtered count display
    document.getElementById('filteredCount').textContent = filteredCount;
    document.getElementById('totalRecords').textContent = currentVoters.length;
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('genderFilter').value = '';
    document.getElementById('pageFilter').value = '';
    renderTable();
}

// Populate page filter dropdown with unique page numbers
function populatePageFilter() {
    const pageFilter = document.getElementById('pageFilter');
    if (!pageFilter) return;
    
    // Get unique page numbers
    const pages = [...new Set(currentVoters.map(v => v.page_number).filter(p => p))].sort((a, b) => {
        const numA = parseInt(a) || 0;
        const numB = parseInt(b) || 0;
        return numA - numB;
    });
    
    // Clear existing options except first ("All Pages")
    pageFilter.innerHTML = '<option value="">All Pages</option>';
    
    // Add page options
    pages.forEach(page => {
        const option = document.createElement('option');
        option.value = page;
        option.textContent = `Page ${page}`;
        pageFilter.appendChild(option);
    });
}

// Update statistics cards
function updateStats() {
    const total = currentVoters.length;
    const maleCount = currentVoters.filter(v => v.gender === 'Male').length;
    const femaleCount = currentVoters.filter(v => v.gender === 'Female').length;
    
    // Calculate average age (only for valid numeric ages)
    const validAges = currentVoters
        .map(v => parseInt(v.age))
        .filter(age => !isNaN(age) && age > 0 && age < 150);
    const avgAge = validAges.length > 0 
        ? Math.round(validAges.reduce((a, b) => a + b, 0) / validAges.length) 
        : 0;
    
    // Update DOM
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statMale').textContent = maleCount;
    document.getElementById('statFemale').textContent = femaleCount;
    document.getElementById('statAvgAge').textContent = avgAge;
    document.getElementById('filteredCount').textContent = total;
    document.getElementById('totalRecords').textContent = total;
}

// Keyboard shortcut: Ctrl+F to focus search
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput && document.getElementById('resultsSection').style.display !== 'none') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    }
});

// ============================================
// SORTING FUNCTIONALITY
// ============================================

let currentSortColumn = null;
let currentSortDirection = 'asc';

function sortTable(column) {
    // Toggle direction if same column clicked
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }
    
    // Sort the data
    currentVoters.sort((a, b) => {
        let valA = a[column] || '';
        let valB = b[column] || '';
        
        // Handle numeric columns
        if (column === 'page_number' || column === 'age') {
            valA = parseInt(valA) || 0;
            valB = parseInt(valB) || 0;
        } else {
            // String comparison (case insensitive)
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
        }
        
        if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Update sort indicators
    updateSortIndicators();
    
    // Re-render table
    renderTable();
}

function updateSortIndicators() {
    // Reset all indicators
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.textContent = '⇅';
        indicator.style.opacity = '0.5';
    });
    
    // Update active indicator
    if (currentSortColumn) {
        const activeIndicator = document.querySelector(`.sort-indicator[data-col="${currentSortColumn}"]`);
        if (activeIndicator) {
            activeIndicator.textContent = currentSortDirection === 'asc' ? '↑' : '↓';
            activeIndicator.style.opacity = '1';
        }
    }
}

// ============================================
// VALIDATION STATISTICS
// ============================================

function getValidationStats() {
    const errors = currentVoters.filter(v => !v.epic || v.epic === 'ERROR_MISSING_EPIC').length;
    const warnings = currentVoters.filter(v => 
        (!v.name_marathi && !v.name_english) || 
        (v.age && (parseInt(v.age) < 18 || parseInt(v.age) > 120))
    ).length;
    
    return { errors, warnings };
}

// Update the stats function to include validation counts
const originalUpdateStats = updateStats;
updateStats = function() {
    // Call original function
    const total = currentVoters.length;
    const maleCount = currentVoters.filter(v => v.gender === 'Male').length;
    const femaleCount = currentVoters.filter(v => v.gender === 'Female').length;
    
    // Calculate average age (only for valid numeric ages)
    const validAges = currentVoters
        .map(v => parseInt(v.age))
        .filter(age => !isNaN(age) && age > 0 && age < 150);
    const avgAge = validAges.length > 0 
        ? Math.round(validAges.reduce((a, b) => a + b, 0) / validAges.length) 
        : 0;
    
    // Update DOM
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statMale').textContent = maleCount;
    document.getElementById('statFemale').textContent = femaleCount;
    document.getElementById('statAvgAge').textContent = avgAge;
    document.getElementById('filteredCount').textContent = total;
    document.getElementById('totalRecords').textContent = total;
    
    // Get validation stats
    const validation = getValidationStats();
    
    // Update total count badge with validation info
    const countBadge = document.getElementById('totalCount');
    if (validation.errors > 0 || validation.warnings > 0) {
        let validationText = [];
        if (validation.errors > 0) validationText.push(`${validation.errors} ⚠️`);
        if (validation.warnings > 0) validationText.push(`${validation.warnings} ⚡`);
        countBadge.innerHTML = `${total} voters <span style="font-size: 0.8em; opacity: 0.8;">(${validationText.join(', ')})</span>`;
    } else {
        countBadge.textContent = `${total} voters ✓`;
    }
};
