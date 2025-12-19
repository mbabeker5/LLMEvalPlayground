// API Configuration
const API_URL = 'http://localhost:8000';

// State
let selectedModels = [];
let selectedFile = null;
let availableModels = [];

// DOM Elements
const modelCheckboxes = document.getElementById('modelCheckboxes');
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const fileBadge = document.getElementById('fileBadge');
const fileName = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');
const schemaInput = document.getElementById('schemaInput');
const formatSchema = document.getElementById('formatSchema');
const clearSchema = document.getElementById('clearSchema');
const schemaStatus = document.getElementById('schemaStatus');
const runBtn = document.getElementById('runBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const clearResults = document.getElementById('clearResults');
const errorToast = document.getElementById('errorToast');
const errorMessage = document.getElementById('errorMessage');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadModels();
    setupEventListeners();
    updateRunButtonState();
});

// Load available models from API
async function loadModels() {
    try {
        const response = await fetch(`${API_URL}/models`);
        const data = await response.json();
        availableModels = data.models;
        renderModelCheckboxes();
    } catch (error) {
        console.error('Failed to load models:', error);
        // Fallback models if API is not available
        availableModels = [
            { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash (Preview)', provider: 'google' },
            { id: 'gemini-3-pro-preview', name: 'Gemini 3 Pro (Preview)', provider: 'google' },
            { id: 'gpt-5.2', name: 'GPT-5.2', provider: 'openai' },
            { id: 'gpt-5.2-pro', name: 'GPT-5.2 Pro', provider: 'openai' },
        ];
        renderModelCheckboxes();
    }
}

// Render model checkboxes grouped by provider
function renderModelCheckboxes() {
    // Group models by provider
    const googleModels = availableModels.filter(m => m.provider === 'google');
    const openaiModels = availableModels.filter(m => m.provider === 'openai');
    
    let html = '';
    
    if (googleModels.length > 0) {
        html += `<div class="provider-group">
            <div class="provider-label">
                <span class="provider-badge google">Google</span>
            </div>
            ${googleModels.map(model => renderModelCheckbox(model)).join('')}
        </div>`;
    }
    
    if (openaiModels.length > 0) {
        html += `<div class="provider-group">
            <div class="provider-label">
                <span class="provider-badge openai">OpenAI</span>
            </div>
            ${openaiModels.map(model => renderModelCheckbox(model)).join('')}
        </div>`;
    }
    
    modelCheckboxes.innerHTML = html;
    
    // Add click handlers AFTER HTML is in the DOM
    attachModelClickHandlers();
}

function renderModelCheckbox(model) {
    return `
        <label class="model-checkbox" data-model-id="${model.id}" data-provider="${model.provider}">
            <input type="checkbox" value="${model.id}">
            <span class="checkbox-indicator">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </span>
            <span class="model-name">${model.name}</span>
        </label>
    `;
}

// Attach click handlers to model checkboxes
function attachModelClickHandlers() {
    modelCheckboxes.querySelectorAll('.model-checkbox').forEach(checkbox => {
        checkbox.addEventListener('click', (e) => {
            e.preventDefault();
            const modelId = checkbox.dataset.modelId;
            const input = checkbox.querySelector('input');
            
            if (selectedModels.includes(modelId)) {
                selectedModels = selectedModels.filter(id => id !== modelId);
                checkbox.classList.remove('selected');
                input.checked = false;
            } else {
                selectedModels.push(modelId);
                checkbox.classList.add('selected');
                input.checked = true;
            }
            
            updateRunButtonState();
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // File upload
    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            handleFileSelect(file);
        } else {
            showError('Please upload a PDF file');
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        uploadZone.style.display = 'flex';
        fileBadge.style.display = 'none';
        updateRunButtonState();
    });
    
    // Schema input
    schemaInput.addEventListener('input', validateSchema);
    
    formatSchema.addEventListener('click', () => {
        try {
            const parsed = JSON.parse(schemaInput.value);
            schemaInput.value = JSON.stringify(parsed, null, 2);
            validateSchema();
        } catch (e) {
            showError('Cannot format invalid JSON');
        }
    });
    
    clearSchema.addEventListener('click', () => {
        schemaInput.value = '';
        schemaStatus.textContent = '';
        schemaStatus.className = 'schema-status';
        updateRunButtonState();
    });
    
    // Run button
    runBtn.addEventListener('click', runEvaluation);
    
    // Clear results
    clearResults.addEventListener('click', () => {
        resultsSection.style.display = 'none';
        resultsGrid.innerHTML = '';
    });
}

// Handle file selection
function handleFileSelect(file) {
    if (file.type !== 'application/pdf') {
        showError('Please upload a PDF file');
        return;
    }
    
    selectedFile = file;
    fileName.textContent = file.name;
    uploadZone.style.display = 'none';
    fileBadge.style.display = 'flex';
    updateRunButtonState();
}

// Validate JSON schema
function validateSchema() {
    const value = schemaInput.value.trim();
    
    if (!value) {
        schemaStatus.textContent = '';
        schemaStatus.className = 'schema-status';
        updateRunButtonState();
        return false;
    }
    
    try {
        JSON.parse(value);
        schemaStatus.textContent = '✓ Valid JSON';
        schemaStatus.className = 'schema-status valid';
        updateRunButtonState();
        return true;
    } catch (e) {
        schemaStatus.textContent = '✗ Invalid JSON: ' + e.message;
        schemaStatus.className = 'schema-status invalid';
        updateRunButtonState();
        return false;
    }
}

// Update run button state
function updateRunButtonState() {
    const hasModels = selectedModels.length > 0;
    const hasFile = selectedFile !== null;
    const hasSchema = schemaInput.value.trim() !== '' && validateSchemaQuiet();
    
    runBtn.disabled = !(hasModels && hasFile && hasSchema);
}

// Validate schema without updating UI
function validateSchemaQuiet() {
    try {
        JSON.parse(schemaInput.value);
        return true;
    } catch {
        return false;
    }
}

// Run evaluation
async function runEvaluation() {
    if (!selectedFile || selectedModels.length === 0) return;
    
    // Show loading state
    const btnContent = runBtn.querySelector('.btn-content');
    const btnSpinner = runBtn.querySelector('.btn-spinner');
    runBtn.disabled = true;
    btnContent.style.display = 'none';
    btnSpinner.style.display = 'block';
    
    // Show results section with loading cards
    resultsSection.style.display = 'block';
    resultsGrid.innerHTML = selectedModels.map(modelId => {
        const model = availableModels.find(m => m.id === modelId);
        return `
            <div class="result-card loading" data-model-id="${modelId}">
                <div class="result-card-header">
                    <div class="model-info">
                        <span class="model-label">${model?.name || modelId}</span>
                        <span class="model-id">${modelId}</span>
                    </div>
                    <div class="result-meta">
                        <span class="status-badge">Running</span>
                    </div>
                </div>
                <div class="result-card-body">
                    <div class="loading-spinner"></div>
                </div>
            </div>
        `;
    }).join('');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('models', JSON.stringify(selectedModels));
        formData.append('target_schema', schemaInput.value);
        
        // Send request
        const response = await fetch(`${API_URL}/eval`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderResults(data.results);
        } else {
            showError(data.error || 'Evaluation failed');
            resultsGrid.innerHTML = `
                <div class="result-card error">
                    <div class="result-card-header">
                        <span class="model-label">Error</span>
                        <span class="status-badge error">Failed</span>
                    </div>
                    <div class="result-card-body">
                        <div class="result-error">${data.error || 'Unknown error'}</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        showError(`Error: ${error.message}. Make sure the backend server is running.`);
        resultsGrid.innerHTML = `
            <div class="result-card error">
                <div class="result-card-header">
                    <span class="model-label">Connection Error</span>
                    <span class="status-badge error">Failed</span>
                </div>
                <div class="result-card-body">
                    <div class="result-error">${error.message}</div>
                </div>
            </div>
        `;
    } finally {
        // Reset button state
        runBtn.disabled = false;
        btnContent.style.display = 'flex';
        btnSpinner.style.display = 'none';
    }
}

// Render results
function renderResults(results) {
    resultsGrid.innerHTML = results.map(result => {
        const isSuccess = result.success;
        const hasJson = result.json_data !== null;
        const content = hasJson 
            ? JSON.stringify(result.json_data, null, 2)
            : result.raw_response || result.error;
        const provider = result.provider || 'unknown';
        
        return `
            <div class="result-card ${isSuccess ? 'success' : 'error'}" data-model-id="${result.model_id}">
                <div class="result-card-header">
                    <div class="model-info">
                        <div class="model-label-row">
                            <span class="provider-badge ${provider}">${provider === 'google' ? 'Google' : 'OpenAI'}</span>
                            <span class="model-label">${result.model_name}</span>
                        </div>
                        <span class="model-id">${result.model_id}</span>
                    </div>
                    <div class="result-meta">
                        <span class="duration">${formatDuration(result.duration_ms)}</span>
                        <span class="status-badge ${isSuccess ? 'success' : 'error'}">
                            ${isSuccess ? 'Success' : 'Error'}
                        </span>
                    </div>
                </div>
                <div class="result-card-body">
                    ${isSuccess 
                        ? `<div class="result-json"><pre>${escapeHtml(content)}</pre></div>`
                        : `<div class="result-error">${escapeHtml(result.error)}</div>`
                    }
                </div>
                ${isSuccess ? `
                    <div class="result-card-footer">
                        <button class="copy-result-btn" onclick="copyResult(this, '${result.model_id}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                            </svg>
                            Copy JSON
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// Copy result to clipboard
async function copyResult(button, modelId) {
    const card = document.querySelector(`.result-card[data-model-id="${modelId}"]`);
    const jsonText = card.querySelector('.result-json pre')?.textContent;
    
    if (!jsonText) return;
    
    try {
        await navigator.clipboard.writeText(jsonText);
        
        // Visual feedback
        const originalHTML = button.innerHTML;
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
            Copied!
        `;
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copied');
        }, 2000);
    } catch (error) {
        showError('Failed to copy to clipboard');
    }
}

// Format duration
function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show error toast
function showError(message) {
    errorMessage.textContent = message;
    errorToast.style.display = 'flex';
    
    setTimeout(() => {
        errorToast.style.display = 'none';
    }, 5000);
}

// Make copyResult available globally
window.copyResult = copyResult;
