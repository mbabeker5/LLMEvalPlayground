// API Configuration
const API_URL = 'http://localhost:8000';

// State
let selectedModels = [];
let selectedFile = null;
let availableModels = [];
let prompts = [];
let schemas = [];
let judges = [];
let runs = [];
let currentRunId = null;
let currentPromptId = null;
let currentSchemaId = null;
let currentRunData = null;
let editingSchemaId = null;

// DOM Elements (will be populated on load)
let elements = {};

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', async () => {
    initializeElements();
    setupNavigation();
    setupEventListeners();
    await loadInitialData();
    updateRunButtonState();
});

function initializeElements() {
    elements = {
        // Nav
        navItems: document.querySelectorAll('.nav-item'),
        views: document.querySelectorAll('.view'),
        
        // Dashboard
        totalRuns: document.getElementById('totalRuns'),
        totalPrompts: document.getElementById('totalPrompts'),
        totalJudges: document.getElementById('totalJudges'),
        recentRunsList: document.getElementById('recentRunsList'),
        
        // Eval
        promptSelect: document.getElementById('promptSelect'),
        modelCheckboxes: document.getElementById('modelCheckboxes'),
        uploadZone: document.getElementById('uploadZone'),
        fileInput: document.getElementById('fileInput'),
        fileBadge: document.getElementById('fileBadge'),
        fileName: document.getElementById('fileName'),
        removeFile: document.getElementById('removeFile'),
        schemaInput: document.getElementById('schemaInput'),
        schemaSelect: document.getElementById('schemaSelect'),
        saveSchemaFromEval: document.getElementById('saveSchemaFromEval'),
        formatSchema: document.getElementById('formatSchema'),
        clearSchema: document.getElementById('clearSchema'),
        schemaStatus: document.getElementById('schemaStatus'),
        runBtn: document.getElementById('runBtn'),
        resultsSection: document.getElementById('resultsSection'),
        resultsGrid: document.getElementById('resultsGrid'),
        clearResults: document.getElementById('clearResults'),
        editPromptBtn: document.getElementById('editPromptBtn'),
        addModelsBtn: document.getElementById('addModelsBtn'),
        judgesPanel: document.getElementById('judgesPanel'),
        judgesPanelGrid: document.getElementById('judgesPanelGrid'),
        
        // History
        historyTableBody: document.getElementById('historyTableBody'),
        runDetailModal: document.getElementById('runDetailModal'),
        runDetailContent: document.getElementById('runDetailContent'),
        
        // Prompts
        promptsList: document.getElementById('promptsList'),
        promptModal: document.getElementById('promptModal'),
        promptModalTitle: document.getElementById('promptModalTitle'),
        promptName: document.getElementById('promptName'),
        promptContent: document.getElementById('promptContent'),
        promptActive: document.getElementById('promptActive'),
        savePromptBtn: document.getElementById('savePromptBtn'),
        
        // Schemas
        schemasList: document.getElementById('schemasList'),
        schemaModal: document.getElementById('schemaModal'),
        schemaModalTitle: document.getElementById('schemaModalTitle'),
        schemaName: document.getElementById('schemaName'),
        schemaContent: document.getElementById('schemaContent'),
        schemaActive: document.getElementById('schemaActive'),
        schemaModalStatus: document.getElementById('schemaModalStatus'),
        formatSchemaModal: document.getElementById('formatSchemaModal'),
        clearSchemaModal: document.getElementById('clearSchemaModal'),
        saveSchemaBtn: document.getElementById('saveSchemaBtn'),
        
        // Judges
        judgesList: document.getElementById('judgesList'),
        judgeModal: document.getElementById('judgeModal'),
        judgeModalTitle: document.getElementById('judgeModalTitle'),
        judgeName: document.getElementById('judgeName'),
        judgeModel: document.getElementById('judgeModel'),
        judgeDescription: document.getElementById('judgeDescription'),
        judgePrompt: document.getElementById('judgePrompt'),
        goldenSet: document.getElementById('goldenSet'),
        saveJudgeBtn: document.getElementById('saveJudgeBtn'),
        
        // Inline Prompt Edit Modal
        inlinePromptModal: document.getElementById('inlinePromptModal'),
        selectExistingPrompt: document.getElementById('selectExistingPrompt'),
        editInlinePrompt: document.getElementById('editInlinePrompt'),
        selectPromptSection: document.getElementById('selectPromptSection'),
        editPromptSection: document.getElementById('editPromptSection'),
        editPromptContentSection: document.getElementById('editPromptContentSection'),
        inlinePromptSelect: document.getElementById('inlinePromptSelect'),
        inlinePromptName: document.getElementById('inlinePromptName'),
        inlinePromptContent: document.getElementById('inlinePromptContent'),
        inlinePromptActive: document.getElementById('inlinePromptActive'),
        saveInlinePromptBtn: document.getElementById('saveInlinePromptBtn'),
        
        // Toasts
        errorToast: document.getElementById('errorToast'),
        errorMessage: document.getElementById('errorMessage'),
        successToast: document.getElementById('successToast'),
        successMessage: document.getElementById('successMessage')
    };
}

async function loadInitialData() {
    try {
        await Promise.all([
            loadModels(),
            loadPrompts(),
            loadSchemas(),
            loadJudges(),
            loadRuns()
        ]);
        updateDashboardStats();
    } catch (error) {
        console.error('Failed to load initial data:', error);
    }
}

// ==================== Navigation ====================

function setupNavigation() {
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            showView(view);
        });
    });
}

function showView(viewName) {
    // Update nav
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });
    
    // Update views
    elements.views.forEach(view => {
        view.classList.toggle('active', view.id === `${viewName}View`);
    });
    
    // Refresh data if needed
    if (viewName === 'history') {
        loadRuns();
    } else if (viewName === 'prompts') {
        loadPrompts();
    } else if (viewName === 'judges') {
        loadJudges();
    } else if (viewName === 'dashboard') {
        updateDashboardStats();
    }
}

// Make showView available globally
window.showView = showView;

// ==================== Data Loading ====================

async function loadModels() {
    try {
        const response = await fetch(`${API_URL}/models`);
        const data = await response.json();
        availableModels = data.models;
        renderModelCheckboxes();
        populateJudgeModelSelect();
    } catch (error) {
        console.error('Failed to load models:', error);
        // Fallback models
        availableModels = [
            { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash (Preview)', provider: 'google' },
            { id: 'gpt-5.2', name: 'GPT-5.2', provider: 'openai' },
        ];
        renderModelCheckboxes();
    }
}

async function loadPrompts() {
    try {
        const response = await fetch(`${API_URL}/prompts`);
        const data = await response.json();
        prompts = data.prompts || [];
        renderPromptsList();
        populatePromptSelect();
    } catch (error) {
        console.error('Failed to load prompts:', error);
        prompts = [];
    }
}

async function loadSchemas() {
    try {
        const response = await fetch(`${API_URL}/schemas`);
        const data = await response.json();
        schemas = data.schemas || [];
        renderSchemasList();
        populateSchemaSelect();
    } catch (error) {
        console.error('Failed to load schemas:', error);
        schemas = [];
    }
}

async function loadJudges() {
    try {
        const response = await fetch(`${API_URL}/judges`);
        const data = await response.json();
        judges = data.judges || [];
        renderJudgesList();
        // Also update judges panel if it's visible
        if (elements.judgesPanelGrid) {
            renderJudgesPanel();
        }
    } catch (error) {
        console.error('Failed to load judges:', error);
        judges = [];
    }
}

async function loadRuns() {
    try {
        const response = await fetch(`${API_URL}/runs?limit=50`);
        const data = await response.json();
        runs = data.runs || [];
        renderHistoryTable();
        renderRecentRuns();
    } catch (error) {
        console.error('Failed to load runs:', error);
        runs = [];
    }
}

// ==================== Dashboard ====================

function updateDashboardStats() {
    elements.totalRuns.textContent = runs.length;
    elements.totalPrompts.textContent = prompts.length;
    elements.totalJudges.textContent = judges.length;
}

function renderRecentRuns() {
    if (!runs.length) {
        elements.recentRunsList.innerHTML = '<div class="empty-state">No runs yet. Start a new evaluation!</div>';
        return;
    }
    
    const recentRuns = runs.slice(0, 5);
    elements.recentRunsList.innerHTML = recentRuns.map(run => {
        const date = new Date(run.created_at).toLocaleDateString();
        const status = run.success_count === run.total_count ? 'success' : 'partial';
        
        return `
            <div class="run-item" onclick="viewRunDetails('${run.id}')">
                <div class="run-item-info">
                    <div class="run-item-title">${run.prompt_name || 'Default Prompt'} v${run.prompt_version || 1}</div>
                    <div class="run-item-meta">${date} • ${run.selected_models.length} models</div>
                </div>
                <div class="run-item-status ${status}">
                    ${run.success_count}/${run.total_count}
                </div>
            </div>
        `;
    }).join('');
}

// ==================== Models ====================

function renderModelCheckboxes() {
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
    
    elements.modelCheckboxes.innerHTML = html;
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

function attachModelClickHandlers() {
    elements.modelCheckboxes.querySelectorAll('.model-checkbox').forEach(checkbox => {
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

function populateJudgeModelSelect() {
    elements.judgeModel.innerHTML = availableModels.map(model => 
        `<option value="${model.id}">${model.name}</option>`
    ).join('');
}

// ==================== Prompts ====================

function populatePromptSelect() {
    const options = ['<option value="">Use Default (from file)</option>'];
    prompts.forEach(prompt => {
        options.push(`<option value="${prompt.id}">${prompt.name} v${prompt.version_number}${prompt.is_active ? ' (Active)' : ''}</option>`);
    });
    elements.promptSelect.innerHTML = options.join('');
}

function renderPromptsList() {
    if (!prompts.length) {
        elements.promptsList.innerHTML = '<div class="empty-state">No prompts yet. Create your first prompt!</div>';
        return;
    }
    
    elements.promptsList.innerHTML = prompts.map(prompt => {
        const preview = prompt.content.substring(0, 200) + (prompt.content.length > 200 ? '...' : '');
        const date = new Date(prompt.created_at).toLocaleDateString();
        
        return `
            <div class="prompt-card">
                <div class="prompt-card-header">
                    <div class="prompt-card-title">
                        <h4>${prompt.name}</h4>
                        <span class="version-badge">v${prompt.version_number}</span>
                        ${prompt.is_active ? '<span class="active-badge">Active</span>' : ''}
                    </div>
                    <div class="prompt-card-actions">
                        <button class="btn-text" onclick="editPrompt('${prompt.id}')">Edit</button>
                        <button class="btn-text" onclick="createNewVersion('${prompt.id}')">New Version</button>
                        <button class="btn-text" style="color: var(--error-color);" onclick="deletePrompt('${prompt.id}')">Delete</button>
                    </div>
                </div>
                <div class="prompt-card-body">
                    <div class="prompt-preview">${escapeHtml(preview)}</div>
                </div>
                <div class="prompt-card-footer">
                    Created ${date} • ${prompt.content.length} characters
                </div>
            </div>
        `;
    }).join('');
}

let editingPromptId = null;

function openPromptModal(promptId = null) {
    editingPromptId = promptId;
    
    if (promptId) {
        const prompt = prompts.find(p => p.id === promptId);
        if (prompt) {
            elements.promptModalTitle.textContent = 'Edit Prompt';
            elements.promptName.value = prompt.name;
            elements.promptContent.value = prompt.content;
            elements.promptActive.checked = prompt.is_active;
        }
    } else {
        elements.promptModalTitle.textContent = 'New Prompt';
        elements.promptName.value = '';
        elements.promptContent.value = '';
        elements.promptActive.checked = false;
    }
    
    elements.promptModal.style.display = 'flex';
}

window.openPromptModal = openPromptModal;

function editPrompt(promptId) {
    openPromptModal(promptId);
}

window.editPrompt = editPrompt;

async function savePrompt() {
    const name = elements.promptName.value.trim();
    const content = elements.promptContent.value.trim();
    const isActive = elements.promptActive.checked;
    
    if (!name || !content) {
        showError('Please fill in all required fields');
        return;
    }
    
    try {
        const url = editingPromptId ? `${API_URL}/prompts/${editingPromptId}` : `${API_URL}/prompts`;
        const method = editingPromptId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content, is_active: isActive })
        });
        
        if (!response.ok) throw new Error('Failed to save prompt');
        
        closeModal('promptModal');
        await loadPrompts();
        showSuccess('Prompt saved successfully');
    } catch (error) {
        showError(error.message);
    }
}

async function createNewVersion(promptId) {
    const prompt = prompts.find(p => p.id === promptId);
    if (!prompt) return;
    
    elements.promptModalTitle.textContent = 'New Version';
    elements.promptName.value = prompt.name;
    elements.promptContent.value = prompt.content;
    elements.promptActive.checked = false;
    editingPromptId = null; // Creating new, not editing
    
    elements.promptModal.style.display = 'flex';
}

window.createNewVersion = createNewVersion;

async function deletePrompt(promptId) {
    if (!confirm('Are you sure you want to delete this prompt?')) return;
    
    try {
        const response = await fetch(`${API_URL}/prompts/${promptId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete prompt');
        
        await loadPrompts();
        showSuccess('Prompt deleted');
    } catch (error) {
        showError(error.message);
    }
}

window.deletePrompt = deletePrompt;

// ==================== Schemas ====================

function renderSchemasList() {
    if (!elements.schemasList) return;
    
    if (!schemas.length) {
        elements.schemasList.innerHTML = '<div class="empty-state">No schemas yet. Create your first schema!</div>';
        return;
    }
    
    const schemaGroups = groupSchemasByLineage(schemas);

    elements.schemasList.innerHTML = schemaGroups.map(group => {
        const latestSchema = group.versions[group.versions.length - 1];
        const hasVersions = group.versions.length > 1;
        const version = latestSchema.version_number || group.versions.length || 1;
        const previewContent = JSON.stringify(latestSchema.schema_content, null, 2);
        const previewLines = previewContent.split('\n').slice(0, 8).join('\n');

        return `
            <div class="prompt-card schema-card" data-schema-group="${group.rootId}">
                <div class="prompt-card-header">
                    <div class="judge-title-row">
                        <h4>${latestSchema.name}</h4>
                        <span class="version-badge">v${version}</span>
                    </div>
                    <div class="prompt-card-actions">
                        <button class="btn-text" onclick="editSchema('${latestSchema.id}')">Edit</button>
                        <button class="btn-text" style="color: var(--error-color);" onclick="deleteSchema('${latestSchema.id}')">Delete</button>
                    </div>
                </div>
                <pre class="schema-preview">${escapeHtml(previewLines)}${previewContent.split('\n').length > 8 ? '\n...' : ''}</pre>
                <div class="prompt-card-meta">
                    <span>Created ${new Date(latestSchema.created_at).toLocaleDateString()}</span>
                </div>
                ${hasVersions ? `
                    <div class="version-history">
                        <button class="version-toggle-btn" onclick="toggleSchemaVersionHistory('${group.rootId}')">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"/>
                            </svg>
                            ${group.versions.length} versions
                        </button>
                        <div class="version-list" id="schema-versions-${group.rootId}" style="display: none;">
                            ${group.versions.slice(0, -1).reverse().map(v => `
                                <div class="version-item">
                                    <span class="version-badge small">v${v.version_number || 1}</span>
                                    <span class="version-date">${new Date(v.created_at).toLocaleDateString()}</span>
                                    <button class="btn-text small" onclick="viewSchemaVersion('${v.id}')">View</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function groupSchemasByLineage(schemaList) {
    const groups = {};
    const schemaMap = {};

    schemaList.forEach(s => {
        schemaMap[s.id] = s;
    });

    schemaList.forEach(schema => {
        let rootId = schema.id;
        let current = schema;

        while (current.parent_schema_id && schemaMap[current.parent_schema_id]) {
            current = schemaMap[current.parent_schema_id];
            rootId = current.id;
        }

        if (!groups[rootId]) {
            groups[rootId] = { rootId, versions: [] };
        }
        groups[rootId].versions.push(schema);
    });

    Object.values(groups).forEach(group => {
        group.versions.sort((a, b) => (a.version_number || 1) - (b.version_number || 1));
    });

    return Object.values(groups).sort((a, b) => {
        const aLatest = a.versions[a.versions.length - 1];
        const bLatest = b.versions[b.versions.length - 1];
        return new Date(bLatest.created_at) - new Date(aLatest.created_at);
    });
}

function toggleSchemaVersionHistory(groupId) {
    const el = document.getElementById(`schema-versions-${groupId}`);
    if (el) {
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
}

function viewSchemaVersion(schemaId) {
    openSchemaModal(schemaId);
}

window.toggleSchemaVersionHistory = toggleSchemaVersionHistory;
window.viewSchemaVersion = viewSchemaVersion;

function populateSchemaSelect() {
    if (!elements.schemaSelect) return;
    
    const options = ['<option value="">Select saved schema...</option>'];
    schemas.forEach(schema => {
        const version = schema.version_number || 1;
        options.push(`<option value="${schema.id}">${schema.name} (v${version})</option>`);
    });
    elements.schemaSelect.innerHTML = options.join('');
}

function openSchemaModal(schemaId = null) {
    editingSchemaId = schemaId;
    
    if (schemaId) {
        const schema = schemas.find(s => s.id === schemaId);
        if (schema) {
            elements.schemaModalTitle.textContent = 'Create New Schema Version';
            elements.schemaName.value = schema.name;
            elements.schemaContent.value = JSON.stringify(schema.schema_content, null, 2);
            elements.schemaActive.checked = schema.is_active || false;
            validateSchemaModal();
        }
    } else {
        elements.schemaModalTitle.textContent = 'New Schema';
        elements.schemaName.value = '';
        elements.schemaContent.value = '';
        elements.schemaActive.checked = false;
        validateSchemaModal();
    }
    
    elements.schemaModal.style.display = 'flex';
}

window.openSchemaModal = openSchemaModal;

function editSchema(schemaId) {
    openSchemaModal(schemaId);
}

window.editSchema = editSchema;

async function saveSchema() {
    const name = elements.schemaName.value.trim();
    const contentStr = elements.schemaContent.value.trim();
    
    if (!name) {
        showError('Please enter a schema name');
        return;
    }
    
    if (!contentStr) {
        showError('Please enter schema content');
        return;
    }
    
    let schemaContent;
    try {
        schemaContent = JSON.parse(contentStr);
    } catch (e) {
        showError('Schema content must be valid JSON');
        return;
    }
    
    try {
        // Always create a new schema (versioning behavior)
        const response = await fetch(`${API_URL}/schemas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                schema_content: schemaContent,
                parent_schema_id: editingSchemaId || null,
                is_active: elements.schemaActive.checked
            })
        });
        
        if (!response.ok) {
            const errText = await response.text();
            throw new Error(errText || 'Failed to save schema');
        }
        
        closeModal('schemaModal');
        await loadSchemas();
        const actionText = editingSchemaId ? 'New schema version created' : 'Schema created successfully';
        showSuccess(actionText);
    } catch (error) {
        showError(error.message);
    }
}

function validateSchemaModal() {
    if (!elements.schemaModalStatus || !elements.schemaContent) return;
    const txt = elements.schemaContent.value.trim();
    if (!txt) {
        elements.schemaModalStatus.textContent = '';
        elements.schemaModalStatus.className = 'schema-status';
        return;
    }
    try {
        JSON.parse(txt);
        elements.schemaModalStatus.textContent = 'Valid JSON';
        elements.schemaModalStatus.className = 'schema-status valid';
    } catch (e) {
        elements.schemaModalStatus.textContent = 'Invalid JSON';
        elements.schemaModalStatus.className = 'schema-status invalid';
    }
}

function formatSchemaModal() {
    const txt = elements.schemaContent.value.trim();
    if (!txt) return;
    try {
        const obj = JSON.parse(txt);
        elements.schemaContent.value = JSON.stringify(obj, null, 2);
        validateSchemaModal();
    } catch (e) {
        showError('Schema content must be valid JSON to format');
    }
}

function clearSchemaModal() {
    elements.schemaContent.value = '';
    validateSchemaModal();
}

async function deleteSchema(schemaId) {
    if (!confirm('Are you sure you want to delete this schema?')) return;
    
    try {
        const response = await fetch(`${API_URL}/schemas/${schemaId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete schema');
        
        await loadSchemas();
        showSuccess('Schema deleted');
    } catch (error) {
        showError(error.message);
    }
}

window.deleteSchema = deleteSchema;

// ==================== Judges ====================

function renderJudgesList() {
    if (!judges.length) {
        elements.judgesList.innerHTML = '<div class="empty-state">No judges yet. Create your first judge template!</div>';
        return;
    }
    
    // Group judges by lineage (root judge)
    const judgeGroups = groupJudgesByLineage(judges);
    
    elements.judgesList.innerHTML = judgeGroups.map(group => {
        const latestJudge = group.versions[group.versions.length - 1];
        const hasVersions = group.versions.length > 1;
        const model = availableModels.find(m => m.id === latestJudge.judge_model);
        const modelName = model ? model.name : latestJudge.judge_model;
        const versionNum = latestJudge.version_number || group.versions.length;
        
        return `
            <div class="judge-card" data-judge-group="${group.rootId}">
                <div class="judge-card-header">
                    <div class="judge-title-row">
                        <h4>${latestJudge.name}</h4>
                        <span class="version-badge">v${versionNum}</span>
                    </div>
                    <div class="prompt-card-actions">
                        <button class="btn-text" onclick="editJudge('${latestJudge.id}')">Edit</button>
                        <button class="btn-text" style="color: var(--error-color);" onclick="deleteJudge('${latestJudge.id}')">Delete</button>
                    </div>
                </div>
                <p class="judge-card-description">${latestJudge.description || 'No description'}</p>
                <div class="judge-card-meta">
                    <span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        </svg>
                        ${modelName}
                    </span>
                    ${latestJudge.golden_set ? '<span>Has Golden Set</span>' : ''}
                </div>
                ${hasVersions ? `
                    <div class="version-history">
                        <button class="version-toggle-btn" onclick="toggleVersionHistory('${group.rootId}')">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"/>
                            </svg>
                            ${group.versions.length} versions
                        </button>
                        <div class="version-list" id="versions-${group.rootId}" style="display: none;">
                            ${group.versions.slice(0, -1).reverse().map(v => `
                                <div class="version-item">
                                    <span class="version-badge small">v${v.version_number || 1}</span>
                                    <span class="version-date">${new Date(v.created_at).toLocaleDateString()}</span>
                                    <button class="btn-text small" onclick="viewJudgeVersion('${v.id}')">View</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function groupJudgesByLineage(judgesList) {
    // Find root judges (those without parent_judge_id) and group all versions
    const groups = {};
    const judgeMap = {};
    
    // Build a map of all judges
    judgesList.forEach(j => {
        judgeMap[j.id] = j;
    });
    
    // Find root for each judge and group
    judgesList.forEach(judge => {
        let rootId = judge.id;
        let current = judge;
        
        // Traverse up to find root
        while (current.parent_judge_id && judgeMap[current.parent_judge_id]) {
            current = judgeMap[current.parent_judge_id];
            rootId = current.id;
        }
        
        if (!groups[rootId]) {
            groups[rootId] = { rootId, versions: [] };
        }
        groups[rootId].versions.push(judge);
    });
    
    // Sort versions within each group by version_number
    Object.values(groups).forEach(group => {
        group.versions.sort((a, b) => (a.version_number || 1) - (b.version_number || 1));
    });
    
    // Sort groups by latest version's created_at
    return Object.values(groups).sort((a, b) => {
        const aLatest = a.versions[a.versions.length - 1];
        const bLatest = b.versions[b.versions.length - 1];
        return new Date(bLatest.created_at) - new Date(aLatest.created_at);
    });
}

function toggleVersionHistory(groupId) {
    const versionList = document.getElementById(`versions-${groupId}`);
    if (versionList) {
        versionList.style.display = versionList.style.display === 'none' ? 'block' : 'none';
    }
}

function viewJudgeVersion(judgeId) {
    const judge = judges.find(j => j.id === judgeId);
    if (judge) {
        openJudgeModal(judgeId);
    }
}

window.toggleVersionHistory = toggleVersionHistory;
window.viewJudgeVersion = viewJudgeVersion;

let editingJudgeId = null;

function openJudgeModal(judgeId = null) {
    editingJudgeId = judgeId;
    
    // Ensure judge model select is populated
    populateJudgeModelSelect();
    
    if (judgeId) {
        const judge = judges.find(j => j.id === judgeId);
        if (judge) {
            elements.judgeModalTitle.textContent = 'Create New Judge Version';
            elements.judgeName.value = judge.name;
            elements.judgeModel.value = judge.judge_model;
            elements.judgeDescription.value = judge.description || '';
            elements.judgePrompt.value = judge.judge_prompt;
            elements.goldenSet.value = judge.golden_set ? JSON.stringify(judge.golden_set, null, 2) : '';
        }
    } else {
        elements.judgeModalTitle.textContent = 'New Judge';
        elements.judgeName.value = '';
        elements.judgeDescription.value = '';
        elements.judgePrompt.value = getDefaultJudgePrompt();
        elements.goldenSet.value = '';
    }
    
    elements.judgeModal.style.display = 'flex';
}

window.openJudgeModal = openJudgeModal;

function getDefaultJudgePrompt() {
    return `Evaluate the following model output against the provided schema and criteria.

## Model Output
{{model_output}}

## Expected Schema
{{schema}}

## Golden Set (Expected Output)
{{golden_set}}

## Evaluation Criteria
1. Schema Compliance: Does the output match the expected schema structure?
2. Data Accuracy: Are the extracted values correct and complete?
3. Formatting: Is the JSON properly formatted?

Provide your evaluation as a JSON object with:
- passed: true/false
- score: 0-100
- reasoning: detailed explanation
- issues: list of specific issues found (if any)`;
}

function editJudge(judgeId) {
    openJudgeModal(judgeId);
}

window.editJudge = editJudge;

async function saveJudge() {
    const name = elements.judgeName.value.trim();
    const judgeModel = elements.judgeModel.value;
    const description = elements.judgeDescription.value.trim();
    const judgePrompt = elements.judgePrompt.value.trim();
    const goldenSetStr = elements.goldenSet.value.trim();
    
    if (!name || !judgeModel || !judgePrompt) {
        showError('Please fill in all required fields');
        return;
    }
    
    let goldenSet = null;
    if (goldenSetStr) {
        try {
            goldenSet = JSON.parse(goldenSetStr);
        } catch (e) {
            showError('Golden set must be valid JSON');
            return;
        }
    }
    
    try {
        // Always create a new judge (versioning behavior - edits become new versions)
        const payload = {
            name,
            judge_model: judgeModel,
            description,
            judge_prompt: judgePrompt,
            golden_set: goldenSet,
            input_variables: ['model_output', 'schema', 'golden_set', 'original_prompt']
        };
        
        // If editing, include parent_judge_id for versioning
        if (editingJudgeId) {
            payload.parent_judge_id = editingJudgeId;
        }
        
        const response = await fetch(`${API_URL}/judges`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to save judge');
        
        closeModal('judgeModal');
        await loadJudges();
        const actionText = editingJudgeId ? 'New judge version created' : 'Judge created successfully';
        showSuccess(actionText);
    } catch (error) {
        showError(error.message);
    }
}

async function deleteJudge(judgeId) {
    if (!confirm('Are you sure you want to delete this judge?')) return;
    
    try {
        const response = await fetch(`${API_URL}/judges/${judgeId}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete judge');
        
        await loadJudges();
        showSuccess('Judge deleted');
    } catch (error) {
        showError(error.message);
    }
}

window.deleteJudge = deleteJudge;

// ==================== History ====================

function renderHistoryTable() {
    if (!runs.length) {
        elements.historyTableBody.innerHTML = '<tr class="empty-row"><td colspan="6">No runs yet. Start a new evaluation!</td></tr>';
        return;
    }
    
    elements.historyTableBody.innerHTML = runs.map(run => {
        const date = new Date(run.created_at).toLocaleString();
        const status = run.success_count === run.total_count ? 'success' : (run.success_count > 0 ? 'partial' : 'error');
        
        return `
            <tr>
                <td>${date}</td>
                <td>${run.prompt_name || 'Default'} v${run.prompt_version || 1}</td>
                <td>${run.document_name || 'Unknown'}</td>
                <td>${run.selected_models.length} models</td>
                <td>
                    <span class="status-badge ${status}">
                        ${run.success_count}/${run.total_count}
                    </span>
                </td>
                <td>
                    <button class="btn-text" onclick="viewRunDetails('${run.id}')">View</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function viewRunDetails(runId) {
    try {
        const response = await fetch(`${API_URL}/runs/${runId}`);
        const data = await response.json();
        
        currentRunId = runId;
        currentRunData = {
            promptVersionId: data.run.prompt_version_id,
            schema: JSON.stringify(data.run.schema_content || {}, null, 2),
            selectedModels: data.results.map(r => r.model_id)
        };
        
        const run = data.run;
        const results = data.results;
        
        // Collect which judges have been applied
        const appliedJudgeIds = new Set();
        results.forEach(r => {
            if (r.judge_results) {
                r.judge_results.forEach(jr => {
                    if (jr.judge_id) appliedJudgeIds.add(jr.judge_id);
                });
            }
        });
        
        // Build judges panel HTML for modal
        const judgesPanelHtml = judges.length > 0 ? `
            <div class="judges-panel modal-judges-panel">
                <div class="judges-panel-header">
                    <h3>Apply Judges</h3>
                    <span class="judges-hint">Click a judge to evaluate outputs</span>
                </div>
                <div class="judges-grid">
                    ${judges.map(judge => {
                        const isApplied = appliedJudgeIds.has(judge.id);
                        return `
                            <button class="judge-apply-btn ${isApplied ? 'applied' : ''}" 
                                    data-judge-id="${judge.id}"
                                    onclick="applyJudgeById('${judge.id}', this)">
                                <span class="judge-btn-name">${escapeHtml(judge.name)}</span>
                                <span class="judge-btn-model">${judge.judge_model}</span>
                                <span class="judge-btn-status ${isApplied ? 'applied' : 'pending'}">
                                    ${isApplied ? '✓ Applied' : 'Click to apply'}
                                </span>
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>
        ` : '';
        
        let html = `
            <div class="run-detail-header">
                <div class="run-detail-meta">
                    <p><strong>Date:</strong> ${new Date(run.created_at).toLocaleString()}</p>
                    <p><strong>Prompt:</strong> ${run.prompt_versions?.name || 'Default'} v${run.prompt_versions?.version_number || 1}</p>
                    <p><strong>Document:</strong> ${run.documents?.filename || 'Unknown'}</p>
                </div>
                <div class="run-detail-actions">
                    <button class="btn-secondary btn-icon" onclick="editPromptFromRunDetail('${run.prompt_version_id}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        Edit Prompt
                    </button>
                    <button class="btn-secondary btn-icon" onclick="showAddModelsModal()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="16"/>
                            <line x1="8" y1="12" x2="16" y2="12"/>
                        </svg>
                        Add Models
                    </button>
                </div>
            </div>
            <div class="run-detail-results">
                <h4>Results (${results.length} models)</h4>
                <div class="results-grid">
                    ${results.map(result => renderResultCard(result, true)).join('')}
                </div>
            </div>
            ${judgesPanelHtml}
        `;
        
        elements.runDetailContent.innerHTML = html;
        elements.runDetailModal.style.display = 'flex';
    } catch (error) {
        showError('Failed to load run details');
    }
}

async function editPromptFromRunDetail(promptVersionId) {
    currentPromptId = promptVersionId;
    closeModal('runDetailModal');
    await editPromptFromResults();
}

window.editPromptFromRunDetail = editPromptFromRunDetail;

window.viewRunDetails = viewRunDetails;

// ==================== Evaluation ====================

function setupEventListeners() {
    // File upload
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    
    elements.uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
        elements.uploadZone.classList.add('drag-over');
    });
    
    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('drag-over');
    });
    
    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        handleFileSelect(file);
    } else {
        showError('Please upload a PDF file');
    }
});

    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    elements.removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        elements.fileInput.value = '';
        elements.uploadZone.style.display = 'flex';
        elements.fileBadge.style.display = 'none';
        updateRunButtonState();
    });
    
    // Schema input
    elements.schemaInput.addEventListener('input', validateSchema);
    
    // Schema select dropdown
    elements.schemaSelect.addEventListener('change', (e) => {
        const schemaId = e.target.value;
        if (schemaId) {
            const schema = schemas.find(s => s.id === schemaId);
            if (schema) {
                currentSchemaId = schemaId;
                elements.schemaInput.value = JSON.stringify(schema.schema_content, null, 2);
                validateSchema();
            }
        } else {
            currentSchemaId = null;
        }
    });
    
    // Save schema from eval view
    elements.saveSchemaFromEval.addEventListener('click', () => {
        const content = elements.schemaInput.value.trim();
        if (!content) {
            showError('Please enter a schema first');
            return;
        }
        try {
            JSON.parse(content);
            // Open schema modal with current content
            elements.schemaModalTitle.textContent = 'Save Schema';
            elements.schemaName.value = '';
            elements.schemaContent.value = content;
            elements.schemaModal.style.display = 'flex';
        } catch (e) {
            showError('Schema must be valid JSON before saving');
        }
    });
    
    elements.formatSchema.addEventListener('click', () => {
        try {
            const parsed = JSON.parse(elements.schemaInput.value);
            elements.schemaInput.value = JSON.stringify(parsed, null, 2);
            validateSchema();
        } catch (e) {
            showError('Cannot format invalid JSON');
        }
    });
    
    elements.clearSchema.addEventListener('click', () => {
        elements.schemaInput.value = '';
        elements.schemaStatus.textContent = '';
        elements.schemaStatus.className = 'schema-status';
        elements.schemaSelect.value = '';
        currentSchemaId = null;
        updateRunButtonState();
    });
    
    // Run button
    elements.runBtn.addEventListener('click', runEvaluation);
    
    // Clear results
    elements.clearResults.addEventListener('click', () => {
        elements.resultsSection.style.display = 'none';
        elements.resultsGrid.innerHTML = '';
        currentRunId = null;
    });
    
    // Edit prompt button
    elements.editPromptBtn.addEventListener('click', editPromptFromResults);
    
    // Add models button
    elements.addModelsBtn.addEventListener('click', showAddModelsModal);
    
    // Save buttons
    elements.savePromptBtn.addEventListener('click', savePrompt);
    elements.saveSchemaBtn.addEventListener('click', saveSchema);
    elements.saveJudgeBtn.addEventListener('click', saveJudge);
    elements.saveInlinePromptBtn.addEventListener('click', saveInlinePrompt);

    // Schema modal UX
    if (elements.schemaContent) {
        elements.schemaContent.addEventListener('input', validateSchemaModal);
    }
    if (elements.formatSchemaModal) {
        elements.formatSchemaModal.addEventListener('click', formatSchemaModal);
    }
    if (elements.clearSchemaModal) {
        elements.clearSchemaModal.addEventListener('click', clearSchemaModal);
    }
}

function handleFileSelect(file) {
    if (file.type !== 'application/pdf') {
        showError('Please upload a PDF file');
        return;
    }
    
    selectedFile = file;
    elements.fileName.textContent = file.name;
    elements.uploadZone.style.display = 'none';
    elements.fileBadge.style.display = 'flex';
    updateRunButtonState();
}

function validateSchema() {
    const value = elements.schemaInput.value.trim();
    
    if (!value) {
        elements.schemaStatus.textContent = '';
        elements.schemaStatus.className = 'schema-status';
        updateRunButtonState();
        return false;
    }
    
    try {
        JSON.parse(value);
        elements.schemaStatus.textContent = '✓ Valid JSON';
        elements.schemaStatus.className = 'schema-status valid';
        updateRunButtonState();
        return true;
    } catch (e) {
        elements.schemaStatus.textContent = '✗ Invalid JSON: ' + e.message;
        elements.schemaStatus.className = 'schema-status invalid';
        updateRunButtonState();
        return false;
    }
}

function validateSchemaQuiet() {
    try {
        JSON.parse(elements.schemaInput.value);
        return true;
    } catch {
        return false;
    }
}

function updateRunButtonState() {
    const hasModels = selectedModels.length > 0;
    const hasFile = selectedFile !== null;
    const hasSchema = elements.schemaInput.value.trim() !== '' && validateSchemaQuiet();
    
    elements.runBtn.disabled = !(hasModels && hasFile && hasSchema);
}

async function runEvaluation() {
    if (!selectedFile || selectedModels.length === 0) return;
    
    // Show loading state
    const btnContent = elements.runBtn.querySelector('.btn-content');
    const btnSpinner = elements.runBtn.querySelector('.btn-spinner');
    elements.runBtn.disabled = true;
    btnContent.style.display = 'none';
    btnSpinner.style.display = 'block';
    
    // Show results section with loading cards
    elements.resultsSection.style.display = 'block';
    elements.resultsGrid.innerHTML = selectedModels.map(modelId => {
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
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('models', JSON.stringify(selectedModels));
        formData.append('target_schema', elements.schemaInput.value);
        
        const promptVersionId = elements.promptSelect.value;
        if (promptVersionId) {
            formData.append('prompt_version_id', promptVersionId);
        }
        
        // Send request
        const response = await fetch(`${API_URL}/eval`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentRunId = data.run_id;
            currentPromptId = promptVersionId || null;
            currentRunData = {
                promptVersionId: promptVersionId,
                schema: elements.schemaInput.value,
                selectedModels: [...selectedModels]
            };
            await renderResults(data.results);
            await loadRuns(); // Refresh runs list
        } else {
            showError(data.error || 'Evaluation failed');
            elements.resultsGrid.innerHTML = `
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
        elements.resultsGrid.innerHTML = `
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
        elements.runBtn.disabled = false;
        btnContent.style.display = 'flex';
        btnSpinner.style.display = 'none';
    }
}

async function renderResults(results) {
    elements.resultsGrid.innerHTML = results.map(result => renderResultCard(result)).join('');
    // Ensure judges are loaded before rendering the panel
    if (judges.length === 0) {
        await loadJudges();
    }
    renderJudgesPanel();
}

function renderJudgesPanel(appliedJudgeIds = []) {
    if (!elements.judgesPanelGrid) return;
    
    if (judges.length === 0) {
        elements.judgesPanelGrid.innerHTML = `
            <div class="empty-judges">
                No judges created yet. <a onclick="showView('judges')">Create a judge</a> to evaluate model outputs.
            </div>
        `;
        return;
    }
    
    elements.judgesPanelGrid.innerHTML = judges.map(judge => {
        const isApplied = appliedJudgeIds.includes(judge.id);
        return `
            <button class="judge-apply-btn ${isApplied ? 'applied' : ''}" 
                    data-judge-id="${judge.id}"
                    onclick="applyJudgeById('${judge.id}', this)">
                <span class="judge-btn-name">${escapeHtml(judge.name)}</span>
                <span class="judge-btn-model">${judge.judge_model}</span>
                <span class="judge-btn-status ${isApplied ? 'applied' : 'pending'}">
                    ${isApplied ? '✓ Applied' : 'Click to apply'}
                </span>
            </button>
        `;
    }).join('');
}

async function applyJudgeById(judgeId, button) {
    if (!currentRunId) {
        showError('No active run to judge');
        return;
    }
    
    // Show loading state
    const originalContent = button.innerHTML;
    button.disabled = true;
    button.classList.add('applying');
    button.innerHTML = `
        <span class="judge-btn-name">Judging...</span>
        <span class="judge-btn-model">Please wait</span>
    `;
    
    try {
        const response = await fetch(`${API_URL}/runs/${currentRunId}/judge-all`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ judge_id: judgeId })
        });
        
        const data = await response.json();
        
        if (data.judge_results) {
            showSuccess(`Judge applied to ${data.judge_results.length} results`);
            
            // Update button to show applied
            button.innerHTML = `
                <span class="judge-btn-name">${escapeHtml(judges.find(j => j.id === judgeId)?.name || 'Judge')}</span>
                <span class="judge-btn-model">${judges.find(j => j.id === judgeId)?.judge_model || ''}</span>
                <span class="judge-btn-status applied">✓ Applied</span>
            `;
            button.classList.remove('applying');
            button.classList.add('applied');
            
            // Refresh the run details to show judge results
            await viewRunDetails(currentRunId);
        } else {
            throw new Error(data.error || 'Failed to apply judge');
        }
    } catch (error) {
        showError('Failed to apply judge: ' + error.message);
        button.innerHTML = originalContent;
        button.classList.remove('applying');
    } finally {
        button.disabled = false;
    }
}

window.applyJudgeById = applyJudgeById;

function renderResultCard(result, showJudgeResults = false) {
    const isSuccess = result.success;
    const hasJson = result.json_data !== null || result.output_json !== null;
    const jsonData = result.json_data || result.output_json;
    const content = hasJson 
        ? JSON.stringify(jsonData, null, 2)
        : result.raw_response || result.error;
    const provider = result.provider || 'unknown';
    const modelName = result.model_name || result.model_id;
    const resultId = result.id || result.model_id;
    
    // Build judge results section with full reasoning
    let judgeResultsSection = '';
    if (showJudgeResults && result.judge_results && result.judge_results.length > 0) {
        const judgeItems = result.judge_results.map((jr, index) => {
            const judgeName = jr.judges?.name || 'Judge';
            const uniqueId = `${resultId}-judge-${index}`;
            const issues = jr.evaluation?.issues || [];
            
            return `
                <div class="judge-result-item ${jr.passed ? 'passed' : 'failed'}">
                    <div class="judge-result-header" onclick="toggleJudgeReasoning('${uniqueId}')">
                        <div class="judge-result-summary">
                            <span class="judge-status-icon">${jr.passed ? '✓' : '✗'}</span>
                            <span class="judge-name">${escapeHtml(judgeName)}</span>
                            ${jr.score !== null ? `<span class="judge-score">${jr.score}/100</span>` : ''}
                        </div>
                        <svg class="expand-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                    </div>
                    <div class="judge-reasoning-panel" id="${uniqueId}" style="display: none;">
                        <div class="reasoning-content">
                            <div class="reasoning-label">Reasoning:</div>
                            <div class="reasoning-text">${escapeHtml(jr.reasoning || 'No reasoning provided')}</div>
                            ${issues.length > 0 ? `
                                <div class="issues-section">
                                    <div class="issues-label">Issues Found:</div>
                                    <ul class="issues-list">
                                        ${issues.map(issue => `<li>${escapeHtml(issue)}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        judgeResultsSection = `
            <div class="judge-results-section">
                <div class="judge-results-header">
                    <span class="judge-results-title">Judge Results (${result.judge_results.length})</span>
                </div>
                <div class="judge-results-list">
                    ${judgeItems}
                </div>
            </div>
        `;
    }
    
    return `
        <div class="result-card ${isSuccess ? 'success' : 'error'}" data-model-id="${result.model_id}" data-result-id="${result.id || ''}">
            <div class="result-card-header">
                <div class="model-info">
                    <div class="model-label-row">
                        <span class="provider-badge ${provider}">${provider === 'google' ? 'Google' : 'OpenAI'}</span>
                        <span class="model-label">${modelName}</span>
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
                    ? `<div class="result-json"><pre>${syntaxHighlightJson(content)}</pre></div>`
                    : `<div class="result-error">${escapeHtml(result.error)}</div>`
                }
            </div>
            ${judgeResultsSection}
            <div class="result-card-footer">
                ${isSuccess ? `
                    <button class="copy-result-btn" onclick="copyResult(this, '${result.model_id}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                        Copy JSON
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

function toggleJudgeReasoning(id) {
    const panel = document.getElementById(id);
    if (panel) {
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        
        // Toggle the expand icon
        const header = panel.previousElementSibling;
        if (header) {
            header.classList.toggle('expanded', !isVisible);
        }
    }
}

window.toggleJudgeReasoning = toggleJudgeReasoning;

// ==================== Edit Prompt from Results ====================

async function editPromptFromResults() {
    // Get the current prompt content
    let promptContent = '';
    let promptName = 'New Prompt';
    
    if (currentPromptId) {
        // Find the prompt in our loaded prompts
        const prompt = prompts.find(p => p.id === currentPromptId);
        if (prompt) {
            promptContent = prompt.content || '';
            promptName = prompt.name || 'New Prompt';
        }
    }
    
    // If no prompt was selected (using default), try to read the default
    if (!promptContent) {
        try {
            const response = await fetch(`${API_URL}/system-prompt`);
            if (response.ok) {
                const data = await response.json();
                promptContent = data.system_prompt || '';
                promptName = 'Default System Prompt (Edited)';
            }
        } catch (e) {
            console.error('Failed to fetch default prompt:', e);
        }
    }
    
    // Populate the inline prompt select dropdown
    elements.inlinePromptSelect.innerHTML = '<option value="">Select a prompt...</option>';
    prompts.forEach(prompt => {
        const version = prompt.version_number || 1;
        const isActive = prompt.is_active ? ' (Active)' : '';
        const selected = prompt.id === currentPromptId ? ' selected' : '';
        elements.inlinePromptSelect.innerHTML += `<option value="${prompt.id}"${selected}>${prompt.name} v${version}${isActive}</option>`;
    });
    
    // Pre-fill inline edit fields with current prompt
    elements.inlinePromptName.value = promptName;
    elements.inlinePromptContent.value = promptContent;
    elements.inlinePromptActive.checked = false;
    
    // Set default mode to "select existing"
    elements.selectExistingPrompt.checked = true;
    elements.selectPromptSection.style.display = 'block';
    elements.editPromptSection.style.display = 'none';
    elements.editPromptContentSection.style.display = 'none';
    
    // Show modal without navigating away
    elements.inlinePromptModal.style.display = 'flex';
    
    // Handle mode switching
    elements.selectExistingPrompt.addEventListener('change', function() {
        if (this.checked) {
            elements.selectPromptSection.style.display = 'block';
            elements.editPromptSection.style.display = 'none';
            elements.editPromptContentSection.style.display = 'none';
        }
    });
    
    elements.editInlinePrompt.addEventListener('change', function() {
        if (this.checked) {
            elements.selectPromptSection.style.display = 'none';
            elements.editPromptSection.style.display = 'block';
            elements.editPromptContentSection.style.display = 'block';
        }
    });
}

async function saveInlinePrompt() {
    const isSelectMode = elements.selectExistingPrompt.checked;
    
    if (isSelectMode) {
        // User selected an existing prompt
        const selectedPromptId = elements.inlinePromptSelect.value;
        if (!selectedPromptId) {
            showError('Please select a prompt');
            return;
        }
        
        // Update current prompt ID and reload results if needed
        currentPromptId = selectedPromptId;
        closeModal('inlinePromptModal');
        showSuccess('Prompt updated');
        // Optionally reload results with new prompt
        // For now, just update the selection
    } else {
        // User is creating a new version inline
        const name = elements.inlinePromptName.value.trim();
        const content = elements.inlinePromptContent.value.trim();
        const isActive = elements.inlinePromptActive.checked;
        
        if (!name || !content) {
            showError('Please fill in all required fields');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/prompts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    content,
                    is_active: isActive
                })
            });
            
            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || 'Failed to save prompt');
            }
            
            const data = await response.json();
            await loadPrompts();
            
            // Update current prompt ID to the newly created one
            if (data.prompt && data.prompt.id) {
                currentPromptId = data.prompt.id;
            }
            
            closeModal('inlinePromptModal');
            showSuccess('New prompt version created');
        } catch (error) {
            showError(error.message);
        }
    }
}

window.saveInlinePrompt = saveInlinePrompt;

// ==================== Add Models to Existing Run ====================

function showAddModelsModal() {
    if (!currentRunId || !currentRunData) {
        showError('No active evaluation to add models to');
        return;
    }
    
    // Get models that weren't in the original run
    const usedModels = currentRunData.selectedModels || [];
    const availableToAdd = availableModels.filter(m => !usedModels.includes(m.id));
    
    if (availableToAdd.length === 0) {
        showError('All available models have already been used in this evaluation');
        return;
    }
    
    // Create modal content for adding models
    const modalHtml = `
        <div class="add-models-modal-content">
            <h3>Add Models to Current Evaluation</h3>
            <p class="modal-description">Select additional models to run on the same document and schema.</p>
            <div class="add-models-list">
                ${availableToAdd.map(model => `
                    <label class="add-model-checkbox">
                        <input type="checkbox" value="${model.id}" data-provider="${model.provider}">
                        <span class="provider-badge ${model.provider}">${model.provider === 'google' ? 'Google' : 'OpenAI'}</span>
                        <span class="model-name">${model.name}</span>
                    </label>
                `).join('')}
            </div>
            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeAddModelsModal()">Cancel</button>
                <button class="btn-primary" onclick="runAdditionalModels()">Run Selected Models</button>
            </div>
        </div>
    `;
    
    // Create or update the add models modal
    let modal = document.getElementById('addModelsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'addModelsModal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `<div class="modal-content">${modalHtml}</div>`;
    modal.style.display = 'flex';
}

function closeAddModelsModal() {
    const modal = document.getElementById('addModelsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

window.closeAddModelsModal = closeAddModelsModal;

async function runAdditionalModels() {
    const modal = document.getElementById('addModelsModal');
    const checkboxes = modal.querySelectorAll('input[type="checkbox"]:checked');
    const newModels = Array.from(checkboxes).map(cb => cb.value);
    
    if (newModels.length === 0) {
        showError('Please select at least one model');
        return;
    }
    
    closeAddModelsModal();
    
    // Show loading state
    showSuccess(`Running ${newModels.length} additional model(s)...`);
    
    try {
        const response = await fetch(`${API_URL}/runs/${currentRunId}/add-models`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ models: newModels })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update current run data
            currentRunData.selectedModels = [...currentRunData.selectedModels, ...newModels];
            
            showSuccess(`Added ${data.results.length} new model results`);
            
            // Refresh the run details
            await viewRunDetails(currentRunId);
        } else {
            showError(data.error || 'Failed to run additional models');
        }
    } catch (error) {
        showError('Failed to run additional models: ' + error.message);
    }
}

window.runAdditionalModels = runAdditionalModels;

// ==================== Utilities ====================

async function copyResult(button, modelId) {
    const card = document.querySelector(`.result-card[data-model-id="${modelId}"]`);
    const jsonText = card.querySelector('.result-json pre')?.textContent;
    
    if (!jsonText) return;
    
    try {
        await navigator.clipboard.writeText(jsonText);
        
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

window.copyResult = copyResult;

function formatDuration(ms) {
    if (!ms) return '0ms';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function syntaxHighlightJson(jsonString) {
    if (!jsonString) return '';
    
    // First escape HTML, then apply syntax highlighting
    const escaped = jsonString
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Apply syntax highlighting with regex
    return escaped.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        (match) => {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    // It's a key
                    cls = 'json-key';
                    // Remove the colon for styling, we'll add it back
                    return `<span class="${cls}">${match.slice(0, -1)}</span><span class="json-colon">:</span>`;
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return `<span class="${cls}">${match}</span>`;
        }
    );
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorToast.style.display = 'flex';
    
    setTimeout(() => {
        elements.errorToast.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    elements.successMessage.textContent = message;
    elements.successToast.style.display = 'flex';
    
    setTimeout(() => {
        elements.successToast.style.display = 'none';
    }, 3000);
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.closeModal = closeModal;
