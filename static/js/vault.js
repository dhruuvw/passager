// PATCHED vault.js - Flask-compatible version

// Global state
let passwords = [];
let currentEditing = null;
let currentPlatform = null;

document.addEventListener('DOMContentLoaded', () => {
    loadPasswords();
    initializeListeners();
    initializeSearch();
});

// ------------------- Core Functionalities -------------------

// Load passwords from /api/fetch_passwords
async function loadPasswords() {
    const masterPassword = sessionStorage.getItem('masterPassword');
    console.log('Debug: masterPassword from sessionStorage:', masterPassword ? 'exists' : 'missing');
    if (!masterPassword) {
        console.error('Debug: Master password is missing from sessionStorage');
        showNotification('Master password missing. Please log in again.', 'error');
        return;
    }

    try {
        showLoading();
        const response = await fetch('/api/fetch_passwords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ master_password: masterPassword })
        });

        const result = await response.json();
        console.log('Debug: fetch_passwords response:', result);
        if (response.ok) {
            passwords = result.passwords || [];
            console.log('Debug: loaded passwords count:', passwords.length);
            displayPasswords(passwords);
        } else {
            console.error('Debug: fetch_passwords failed:', result);
            showNotification(result.message || 'Failed to load passwords', 'error');
        }
    } catch (err) {
        showNotification('Error loading passwords', 'error');
        console.error(err);
    } finally {
        hideLoading();
    }
}

// Save new password to /api/save_password
async function savePassword() {
    const masterPassword = sessionStorage.getItem('masterPassword');
    if (!masterPassword) {
        showNotification('Session expired. Please log in again.', 'error');
        return;
    }

    const form = document.getElementById('password-form');
    const platform = document.getElementById('service-name').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!platform || !password) {
        showNotification('Service and password are required', 'error');
        return;
    }

    try {
        showLoading();
        const response = await fetch('/api/save_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                platform: platform,
                username: username,
                password: password,
                master_password: masterPassword
            })
        });

        const result = await response.json();
        if (response.ok) {
            showNotification(result.message || 'Password saved', 'success');
            closePasswordModal();
            loadPasswords();
        } else {
            showNotification(result.message || 'Failed to save password', 'error');
        }
    } catch (err) {
        showNotification('Error saving password', 'error');
        console.error(err);
    } finally {
        hideLoading();
    }
}

// Delete password via /api/delete_password
async function confirmDelete() {
    if (!currentPlatform) return;

    try {
        showLoading();
        const response = await fetch('/api/delete_password', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ platform: currentPlatform })
        });

        const result = await response.json();
        if (response.ok) {
            showNotification(result.message || 'Deleted successfully', 'success');
            closeConfirmDeleteModal();
            loadPasswords();
        } else {
            showNotification(result.message || 'Failed to delete password', 'error');
        }
    } catch (err) {
        showNotification('Error deleting password', 'error');
        console.error(err);
    } finally {
        hideLoading();
    }
}

// ------------------- UI Functions -------------------

function displayPasswords(passwordList) {
    console.log('Debug: displayPasswords called with:', passwordList);
    const tbody = document.getElementById('password-list');
    const table = document.querySelector('.vault-table-container');
    const empty = document.getElementById('no-passwords');

    // Handle null or undefined passwordList
    if (!passwordList || !Array.isArray(passwordList)) {
        console.error('Debug: passwordList is null, undefined, or not an array:', passwordList);
        if (table) table.style.display = 'none';
        if (empty) empty.style.display = 'block';
        return;
    }

    if (!passwordList.length) {
        console.log('Debug: passwordList is empty');
        if (table) table.style.display = 'none';
        if (empty) empty.style.display = 'block';
        return;
    }

    if (table) table.style.display = 'block';
    if (empty) empty.style.display = 'none';

    if (tbody) {
        tbody.innerHTML = passwordList.map(item => {
            // Add null safety for item properties
            const password = item.password || '';
            const platform = item.platform || 'Unknown';
            const username = item.username || '';
            
            const maskedPassword = '•'.repeat(Math.min(password.length, 12));
            const favicon = getFaviconForService(platform);
            
            return `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            ${favicon}
                            <span>${platform}</span>
                        </div>
                    </td>
                    <td>${username || 'No username'}</td>
                    <td><span style="font-family: monospace; letter-spacing: 2px;">${maskedPassword}</span></td>
                    <td class="actions">
                        <button class="btn-icon" onclick="copyToClipboard('${password.replace(/'/g, "\\'")}')" title="Copy Password">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn-icon" onclick="editPassword('${platform.replace(/'/g, "\\'")}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="deletePasswordPrompt('${platform.replace(/'/g, "\\'")}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }
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
    
    // Check if service name matches any known icons
    for (const [service, icon] of Object.entries(iconMap)) {
        if (serviceName.includes(service)) {
            return icon;
        }
    }
    
    // Default icon
    return '<i class="fas fa-globe" style="color: #6b7280;"></i>';
}

function viewPassword(platform) {
    const item = passwords.find(p => p.platform === platform);
    if (!item) return;

    document.getElementById('detail-service').textContent = item.platform;
    document.getElementById('detail-username').textContent = item.username || 'N/A';
    document.getElementById('detail-password').value = item.password;
    document.getElementById('detail-modal').style.display = 'flex';
    currentPlatform = platform;
}

function editPassword(platform) {
    const item = passwords.find(p => p.platform === platform);
    if (!item) return;

    document.getElementById('service-name').value = item.platform;
    document.getElementById('username').value = item.username;
    document.getElementById('password').value = item.password;

    document.getElementById('modal-title').textContent = 'Edit Password';
    document.getElementById('password-modal').style.display = 'flex';
}

function deletePasswordPrompt(platform) {
    currentPlatform = platform;
    document.getElementById('delete-service-name').textContent = platform;
    document.getElementById('confirm-delete-modal').style.display = 'flex';
}

// ------------------- Helpers -------------------

function initializeListeners() {
    const addPasswordBtn = document.getElementById('add-password-btn');
    if (addPasswordBtn) {
        addPasswordBtn.onclick = () => {
            document.getElementById('password-form').reset();
            document.getElementById('modal-title').textContent = 'Add Password';
            document.getElementById('password-modal').style.display = 'flex';
        };
    }

    // This element doesn't exist in the HTML, so check before accessing
    const generatePasswordBtn = document.getElementById('generate-password-btn');
    if (generatePasswordBtn) {
        generatePasswordBtn.onclick = () => {
            generatePasswordForForm();
        };
    }

    const passwordLengthSlider = document.getElementById('password-length');
    if (passwordLengthSlider) {
        passwordLengthSlider.oninput = function () {
            const lengthValue = document.getElementById('length-value');
            if (lengthValue) {
                lengthValue.textContent = this.value;
            }
        };
    }
}

function generatePasswordForForm() {
    const passwordLengthEl = document.getElementById('password-length');
    const length = parseInt(passwordLengthEl?.value || 12);
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()';
    let pwd = '';
    for (let i = 0; i < length; i++) {
        pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const passwordEl = document.getElementById('password');
    const generatedPasswordEl = document.getElementById('generated-password');
    
    if (passwordEl) passwordEl.value = pwd;
    if (generatedPasswordEl) generatedPasswordEl.value = pwd;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'error');
        console.error(err);
    });
}

function closePasswordModal() {
    document.getElementById('password-modal').style.display = 'none';
}

function closeConfirmDeleteModal() {
    document.getElementById('confirm-delete-modal').style.display = 'none';
    currentPlatform = null;
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showNotification(message, type = 'info') {
    const container = document.createElement('div');
    container.className = `flash-message flash-${type}`;
    container.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">×</button>`;
    document.body.appendChild(container);
    setTimeout(() => container.remove(), 4000);
}

// Additional modal functions
function openAddPasswordModal() {
    document.getElementById('password-form').reset();
    document.getElementById('modal-title').textContent = 'Add Password';
    document.getElementById('password-modal').style.display = 'flex';
}

function openGeneratorModal() {
    document.getElementById('generator-modal').style.display = 'flex';
    generateNewPassword();
}

function closeGeneratorModal() {
    document.getElementById('generator-modal').style.display = 'none';
}

function closeDetailModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

function generateNewPassword() {
    const length = parseInt(document.getElementById('password-length')?.value || 12);
    const includeUppercase = document.getElementById('include-uppercase')?.checked;
    const includeLowercase = document.getElementById('include-lowercase')?.checked;
    const includeNumbers = document.getElementById('include-numbers')?.checked;
    const includeSymbols = document.getElementById('include-symbols')?.checked;
    const excludeChars = document.getElementById('exclude-chars')?.value || '';
    
    let chars = '';
    if (includeUppercase) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (includeLowercase) chars += 'abcdefghijklmnopqrstuvwxyz';
    if (includeNumbers) chars += '0123456789';
    if (includeSymbols) chars += '!@#$%^&*()';
    
    // Remove excluded characters
    for (const char of excludeChars) {
        chars = chars.replace(new RegExp(char, 'g'), '');
    }
    
    if (!chars) {
        showNotification('Please select at least one character type', 'error');
        return;
    }
    
    let password = '';
    for (let i = 0; i < length; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    const generatedField = document.getElementById('generated-password');
    if (generatedField) {
        generatedField.value = password;
    }
}

function copyGeneratedPassword() {
    const generatedField = document.getElementById('generated-password');
    if (generatedField && generatedField.value) {
        copyToClipboard(generatedField.value);
    }
}

function copyDetailPassword() {
    const detailField = document.getElementById('detail-password');
    if (detailField && detailField.value) {
        copyToClipboard(detailField.value);
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

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const filteredPasswords = passwords.filter(item => 
                item.platform.toLowerCase().includes(query) ||
                (item.username && item.username.toLowerCase().includes(query))
            );
            displayPasswords(filteredPasswords);
        });
    }
}

