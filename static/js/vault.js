// ===== MULTI-VAULT PASSWORD MANAGER =====
// Global State
let masterPassword = '';
let currentVaultId = null;
let allVaults = [];
let currentVaultPasswords = [];
let currentPasswordId = null;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeVaultInterface();
});

function initializeVaultInterface() {
    showMasterPasswordModal();
    initializeEventListeners();
    initializePasswordGenerator();
}

function initializeEventListeners() {
    const masterPasswordInput = document.getElementById('master-password-input');
    if (masterPasswordInput) {
        masterPasswordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                unlockVaults();
            }
        });
    }
    
    const vaultSearchInput = document.getElementById('search-input');
    if (vaultSearchInput) {
        vaultSearchInput.addEventListener('input', debounce(filterVaults, 300));
    }
    
    const passwordSearchInput = document.getElementById('password-search-input');
    if (passwordSearchInput) {
        passwordSearchInput.addEventListener('input', debounce(filterPasswords, 300));
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function initializePasswordGenerator() {
    const lengthSlider = document.getElementById('password-length');
    const lengthValue = document.getElementById('length-value');
    
    if (lengthSlider && lengthValue) {
        lengthSlider.addEventListener('input', function() {
            lengthValue.textContent = this.value;
        });
    }
}

// ===== MASTER PASSWORD & AUTHENTICATION =====

function showMasterPasswordModal() {
    const modal = document.getElementById('master-password-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        
        const input = document.getElementById('master-password-input');
        if (input) {
            setTimeout(() => input.focus(), 100);
        }
    }
}

function unlockVaults() {
    const input = document.getElementById('master-password-input');
    const errorDiv = document.getElementById('master-password-error');
    
    if (!input || !input.value.trim()) {
        showError(errorDiv, 'Please enter your master password');
        return;
    }
    
    masterPassword = input.value.trim();
    hideError(errorDiv);
    showLoading(true);
    
    loadVaults()
        .then(() => {
            document.getElementById('master-password-modal').style.display = 'none';
            document.getElementById('vault-main').style.display = 'block';
            showLoading(false);
        })
        .catch((error) => {
            console.error('Failed to load vaults:', error);
            showError(errorDiv, 'Failed to load vaults. Please check your master password.');
            showLoading(false);
        });
}

// ===== VAULT MANAGEMENT =====

async function loadVaults() {
    try {
        const response = await fetch('/api/vaults', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            allVaults = data.vaults;
            renderVaults(allVaults);
            return Promise.resolve();
        } else {
            throw new Error(data.message || 'Failed to load vaults');
        }
    } catch (error) {
        console.error('Error loading vaults:', error);
        throw error;
    }
}

function renderVaults(vaults) {
    const vaultGrid = document.getElementById('vault-grid');
    
    if (!vaults || vaults.length === 0) {
        vaultGrid.innerHTML = `
            <div class="empty-vault">
                <i class="fas fa-vault"></i>
                <h3>No Vaults Yet</h3>
                <p>Create your first vault to start organizing your passwords</p>
                <button class="btn btn-primary" onclick="openCreateVaultModal()">
                    <i class="fas fa-plus"></i> Create First Vault
                </button>
            </div>
        `;
        return;
    }
    
    vaultGrid.innerHTML = vaults.map(vault => `
        <div class="vault-card" onclick="openVault('${vault.id}')">
            <div class="vault-card-header">
                <div class="vault-icon">
                    <i class="fas fa-folder-open"></i>
                </div>
                <div class="vault-menu">
                    <button class="vault-menu-btn" onclick="event.stopPropagation(); deleteVault('${vault.id}')" title="Delete Vault">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="vault-card-body">
                <h3 class="vault-name">${escapeHtml(vault.name)}</h3>
                <p class="vault-description">${escapeHtml(vault.description || 'No description')}</p>
                <div class="vault-stats">
                    <span class="password-count">
                        <i class="fas fa-key"></i> ${vault.password_count} password${vault.password_count !== 1 ? 's' : ''}
                    </span>
                    <span class="vault-updated">
                        Updated ${formatDate(vault.updated_at)}
                    </span>
                </div>
            </div>
            <div class="vault-card-footer">
                <button class="add-password-btn" onclick="event.stopPropagation(); openAddPasswordModal('${vault.id}')">
                    <i class="fas fa-plus"></i> Add Password
                </button>
            </div>
        </div>
    `).join('');
}

function filterVaults() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    
    if (!searchTerm) {
        renderVaults(allVaults);
        return;
    }
    
    const filtered = allVaults.filter(vault => 
        vault.name.toLowerCase().includes(searchTerm) ||
        (vault.description && vault.description.toLowerCase().includes(searchTerm))
    );
    
    renderVaults(filtered);
}

function openCreateVaultModal() {
    const modal = document.getElementById('create-vault-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        
        document.getElementById('vault-name').value = '';
        document.getElementById('vault-description').value = '';
        
        setTimeout(() => document.getElementById('vault-name').focus(), 100);
    }
}

function closeCreateVaultModal() {
    const modal = document.getElementById('create-vault-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

async function createVault() {
    const nameInput = document.getElementById('vault-name');
    const descriptionInput = document.getElementById('vault-description');
    
    const name = nameInput.value.trim();
    const description = descriptionInput.value.trim();
    
    if (!name) {
        showNotification('Please enter a vault name', 'error');
        nameInput.focus();
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/vaults', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Vault "${name}" created successfully!`, 'success');
            closeCreateVaultModal();
            await loadVaults();
        } else {
            showNotification(data.message || 'Failed to create vault', 'error');
        }
    } catch (error) {
        console.error('Error creating vault:', error);
        showNotification('Failed to create vault', 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteVault(vaultId) {
    const vault = allVaults.find(v => v.id === vaultId);
    if (!vault) return;
    
    const confirmMessage = vault.password_count > 0 
        ? `Are you sure you want to delete "${vault.name}"? This will also delete ${vault.password_count} password(s).`
        : `Are you sure you want to delete "${vault.name}"?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`/api/vaults/${vaultId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Vault "${vault.name}" deleted successfully`, 'success');
            await loadVaults();
        } else {
            showNotification(data.message || 'Failed to delete vault', 'error');
        }
    } catch (error) {
        console.error('Error deleting vault:', error);
        showNotification('Failed to delete vault', 'error');
    } finally {
        showLoading(false);
    }
}

// ===== VAULT DETAIL VIEW =====

function showVaultGrid() {
    document.getElementById('vault-detail').style.display = 'none';
    document.getElementById('vault-main').style.display = 'block';
    currentVaultId = null;
    currentVaultPasswords = [];
}

async function openVault(vaultId) {
    const vault = allVaults.find(v => v.id === vaultId);
    if (!vault) return;
    
    currentVaultId = vaultId;
    
    document.getElementById('vault-detail-title').textContent = vault.name;
    document.getElementById('vault-detail-description').textContent = vault.description || 'No description';
    
    document.getElementById('vault-main').style.display = 'none';
    document.getElementById('vault-detail').style.display = 'block';
    
    await loadVaultPasswords(vaultId);
}

async function loadVaultPasswords(vaultId) {
    showLoading(true);
    
    try {
        const response = await fetch(`/api/vaults/${vaultId}/passwords?master_password=${encodeURIComponent(masterPassword)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentVaultPasswords = data.passwords || [];
            renderVaultPasswords(currentVaultPasswords);
        } else {
            showNotification(data.message || 'Failed to load passwords', 'error');
            currentVaultPasswords = [];
            renderVaultPasswords(currentVaultPasswords);
        }
    } catch (error) {
        console.error('Error loading vault passwords:', error);
        showNotification('Failed to load passwords', 'error');
        currentVaultPasswords = [];
        renderVaultPasswords(currentVaultPasswords);
    } finally {
        showLoading(false);
    }
}

function renderVaultPasswords(passwords) {
    const tbody = document.getElementById('password-list');
    const table = document.querySelector('.vault-table-container');
    const empty = document.getElementById('no-passwords');
    
    if (!passwords || passwords.length === 0) {
        if (table) table.style.display = 'none';
        if (empty) empty.style.display = 'block';
        return;
    }
    
    if (table) table.style.display = 'block';
    if (empty) empty.style.display = 'none';
    
    if (tbody) {
        tbody.innerHTML = passwords.map(password => {
            // Add null checks for password fields
            const passwordText = password.password || '';
            const platformText = password.platform || 'Unknown Service';
            const maskedPassword = '•'.repeat(Math.min(passwordText.length, 12));
            const favicon = getFaviconForService(platformText);
            const safeId = platformText.replace(/[^a-zA-Z0-9]/g, '_');
            
            return `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            ${favicon}
                            <span>${escapeHtml(platformText)}</span>
                        </div>
                    </td>
                    <td>${escapeHtml(password.username || 'No username')}</td>
                    <td>
                        <div class="password-cell">
                            <span id="password-display-${safeId}" class="password-display">${maskedPassword}</span>
                            <div class="password-actions">
                                <button class="btn-icon eye-btn" onclick="togglePasswordView('${platformText.replace(/'/g, "\\'")}', '${passwordText.replace(/'/g, "\\'")}', '${safeId}')" title="Show/Hide Password">
                                    <i class="fas fa-eye" id="eye-${safeId}"></i>
                                </button>
                            </div>
                        </div>
                    </td>
                    <td class="actions">
                        <button class="btn-icon copy-btn" onclick="copyToClipboard('${passwordText.replace(/'/g, "\\'")}', 'Password copied!')" title="Copy Password">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn-icon edit-btn" onclick="editPassword('${platformText.replace(/'/g, "\\'")}', '${currentVaultId}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon delete-btn" onclick="deletePasswordPrompt('${platformText.replace(/'/g, "\\'")}', '${currentVaultId}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }
}

function filterPasswords() {
    const searchTerm = document.getElementById('password-search-input').value.toLowerCase();
    
    if (!searchTerm) {
        renderVaultPasswords(currentVaultPasswords);
        return;
    }
    
    const filtered = currentVaultPasswords.filter(password => 
        password.platform.toLowerCase().includes(searchTerm) ||
        (password.username && password.username.toLowerCase().includes(searchTerm))
    );
    
    renderVaultPasswords(filtered);
}

// ===== PASSWORD MANAGEMENT =====

function openAddPasswordModal(vaultId = null) {
    if (vaultId) {
        currentVaultId = vaultId;
    }
    
    const modal = document.getElementById('password-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        
        document.getElementById('password-form').reset();
        document.getElementById('modal-title').textContent = 'Add Password';
        
        setTimeout(() => document.getElementById('service-name').focus(), 100);
    }
}

function closePasswordModal() {
    const modal = document.getElementById('password-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

async function savePassword() {
    if (!currentVaultId) {
        showNotification('No vault selected', 'error');
        return;
    }
    
    const platform = document.getElementById('service-name').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const url = document.getElementById('url').value.trim();
    const notes = document.getElementById('notes').value.trim();
    
    if (!platform || !password) {
        showNotification('Service name and password are required', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`/api/vaults/${currentVaultId}/passwords`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform,
                username: username,
                password: password,
                url: url,
                notes: notes,
                master_password: masterPassword
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Password for ${platform} saved successfully!`, 'success');
            closePasswordModal();
            
            await loadVaultPasswords(currentVaultId);
            await loadVaults();
        } else {
            showNotification(data.message || 'Failed to save password', 'error');
        }
    } catch (error) {
        console.error('Error saving password:', error);
        showNotification('Failed to save password', 'error');
    } finally {
        showLoading(false);
    }
}

function editPassword(platform, vaultId) {
    const password = currentVaultPasswords.find(p => p.platform === platform);
    if (!password) return;
    
    currentVaultId = vaultId;
    
    document.getElementById('service-name').value = password.platform;
    document.getElementById('username').value = password.username || '';
    document.getElementById('password').value = password.password;
    document.getElementById('url').value = password.url || '';
    document.getElementById('notes').value = password.notes || '';
    
    document.getElementById('modal-title').textContent = 'Edit Password';
    document.getElementById('password-modal').style.display = 'flex';
    document.getElementById('password-modal').classList.add('active');
}

function deletePasswordPrompt(platform, vaultId) {
    currentVaultId = vaultId;
    currentPasswordId = platform;
    
    document.getElementById('delete-service-name').textContent = platform;
    document.getElementById('confirm-delete-modal').style.display = 'flex';
    document.getElementById('confirm-delete-modal').classList.add('active');
}

function closeConfirmDeleteModal() {
    const modal = document.getElementById('confirm-delete-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
    currentPasswordId = null;
}

async function confirmDelete() {
    if (!currentPasswordId || !currentVaultId) return;
    
    showLoading(true);
    
    try {
        const response = await fetch(`/api/vaults/${currentVaultId}/passwords/${currentPasswordId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`Password for ${currentPasswordId} deleted successfully`, 'success');
            closeConfirmDeleteModal();
            
            await loadVaultPasswords(currentVaultId);
            await loadVaults();
        } else {
            showNotification(data.message || 'Failed to delete password', 'error');
        }
    } catch (error) {
        console.error('Error deleting password:', error);
        showNotification('Failed to delete password', 'error');
    } finally {
        showLoading(false);
    }
}

// ===== PASSWORD GENERATOR =====

function openGeneratorModal() {
    const modal = document.getElementById('generator-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        generateNewPassword();
    }
}

function closeGeneratorModal() {
    const modal = document.getElementById('generator-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

function generateNewPassword() {
    const length = parseInt(document.getElementById('password-length').value);
    const includeUppercase = document.getElementById('include-uppercase').checked;
    const includeLowercase = document.getElementById('include-lowercase').checked;
    const includeNumbers = document.getElementById('include-numbers').checked;
    const includeSymbols = document.getElementById('include-symbols').checked;
    
    let charset = '';
    if (includeUppercase) charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (includeLowercase) charset += 'abcdefghijklmnopqrstuvwxyz';
    if (includeNumbers) charset += '0123456789';
    if (includeSymbols) charset += '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    if (!charset) {
        showNotification('Please select at least one character type', 'error');
        return;
    }
    
    let password = '';
    for (let i = 0; i < length; i++) {
        password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    
    document.getElementById('generated-password').value = password;
}

function generatePasswordForForm() {
    generateNewPassword();
    const generatedPassword = document.getElementById('generated-password').value;
    if (generatedPassword) {
        document.getElementById('password').value = generatedPassword;
        closeGeneratorModal();
    }
}

function copyGeneratedPassword() {
    const passwordField = document.getElementById('generated-password');
    if (passwordField && passwordField.value) {
        copyToClipboard(passwordField.value, 'Generated password copied!');
    }
}

// ===== UTILITY FUNCTIONS =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
}

function getFaviconForService(platform) {
    const serviceName = platform.toLowerCase();
    const iconMap = {
        'google': '<i class="fab fa-google" style="color: #4285f4;"></i>',
        'gmail': '<i class="fab fa-google" style="color: #4285f4;"></i>',
        'facebook': '<i class="fab fa-facebook" style="color: #1877f2;"></i>',
        'twitter': '<i class="fab fa-twitter" style="color: #1da1f2;"></i>',
        'github': '<i class="fab fa-github" style="color: #333;"></i>',
        'dropbox': '<i class="fab fa-dropbox" style="color: #0061ff;"></i>',
        'microsoft': '<i class="fab fa-microsoft" style="color: #00a1f1;"></i>',
        'apple': '<i class="fab fa-apple" style="color: #000;"></i>',
        'amazon': '<i class="fab fa-amazon" style="color: #ff9900;"></i>',
        'netflix': '<i class="fas fa-tv" style="color: #e50914;"></i>',
        'spotify': '<i class="fab fa-spotify" style="color: #1db954;"></i>',
        'linkedin': '<i class="fab fa-linkedin" style="color: #0077b5;"></i>',
        'instagram': '<i class="fab fa-instagram" style="color: #e4405f;"></i>',
        'youtube': '<i class="fab fa-youtube" style="color: #ff0000;"></i>',
        'slack': '<i class="fab fa-slack" style="color: #4a154b;"></i>'
    };
    
    for (const [service, icon] of Object.entries(iconMap)) {
        if (serviceName.includes(service)) {
            return icon;
        }
    }
    
    return '<i class="fas fa-globe" style="color: #6b7280;"></i>';
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    navigator.clipboard.writeText(text).then(() => {
        showNotification(successMessage, 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'error');
        console.error('Copy failed:', err);
    });
}

function togglePasswordView(platform, actualPassword, safeId) {
    const passwordDisplay = document.getElementById(`password-display-${safeId}`);
    const eyeIcon = document.getElementById(`eye-${safeId}`);
    
    if (passwordDisplay && eyeIcon) {
        if (eyeIcon.classList.contains('fa-eye')) {
            passwordDisplay.textContent = actualPassword;
            eyeIcon.className = 'fas fa-eye-slash';
        } else {
            const maskedPassword = '•'.repeat(Math.min(actualPassword.length, 12));
            passwordDisplay.textContent = maskedPassword;
            eyeIcon.className = 'fas fa-eye';
        }
    }
}

function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const eyeIcon = document.getElementById(fieldId + '-eye');
    
    if (field && eyeIcon) {
        if (field.type === 'password') {
            field.type = 'text';
            eyeIcon.className = 'fas fa-eye-slash';
        } else {
            field.type = 'password';
            eyeIcon.className = 'fas fa-eye';
        }
    }
}

// ===== MODAL MANAGEMENT =====

function closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
        modal.classList.remove('active');
    });
}

function showError(errorDiv, message) {
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.style.color = 'red';
        errorDiv.style.marginTop = '10px';
    }
}

function hideError(errorDiv) {
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// ===== GLOBAL FUNCTIONS FOR BASE TEMPLATE =====

function showLoading(show = true) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'info') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
        return;
    }
    
    const container = document.createElement('div');
    container.className = `flash-message flash-${type}`;
    container.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    document.body.appendChild(container);
    setTimeout(() => container.remove(), 4000);
}
