// Function to apply theme-specific styles
function applyThemeStyles(theme) {
    const root = document.documentElement;
    
    if (theme === 'dark') {
        // Ensure dark theme variables are applied
        root.style.setProperty('--primary-color', '#2D3748');
        root.style.setProperty('--bg-white', '#1A202C');
        root.style.setProperty('--bg-light', '#2D3748');
        root.style.setProperty('--bg-secondary', '#4A5568');
        root.style.setProperty('--bg-card', '#2D3748');
        root.style.setProperty('--text-primary', '#F7FAFC');
        root.style.setProperty('--text-secondary', '#E2E8F0');
        root.style.setProperty('--text-muted', '#A0AEC0');
        root.style.setProperty('--text-light', '#718096');
    } else {
        // Ensure light theme variables are applied
        root.style.setProperty('--primary-color', '#1a202c');
        root.style.setProperty('--bg-white', '#FFFFFF');
        root.style.setProperty('--bg-light', '#F8FAFC');
        root.style.setProperty('--bg-secondary', '#F1F5F9');
        root.style.setProperty('--bg-card', '#FFFFFF');
        root.style.setProperty('--text-primary', '#1a202c');
        root.style.setProperty('--text-secondary', '#4A5568');
        root.style.setProperty('--text-muted', '#718096');
        root.style.setProperty('--text-light', '#A0AEC0');
    }
}

function handleThemeChange(event) {
    const newTheme = event.target.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Apply theme-specific styles immediately
    applyThemeStyles(newTheme);
    
    console.log('Theme changed to:', newTheme);
}

function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (!themeToggle) {
        console.log('Theme toggle not found, retrying in 100ms...');
        setTimeout(initializeThemeToggle, 100);
        return;
    }
    
    // Get current theme
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Set toggle state based on current theme
    themeToggle.checked = currentTheme === 'dark';
    
    // Remove any existing event listeners to prevent duplicates
    themeToggle.removeEventListener('change', handleThemeChange);
    
    // Add event listener for theme toggle
    themeToggle.addEventListener('change', handleThemeChange);
    
    console.log('Theme toggle initialized successfully, current theme:', currentTheme);
}

// Theme management - runs immediately to prevent flash
(function() {
    // Get saved theme or default to light
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply theme immediately to prevent flash
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Apply theme-specific styles immediately
    applyThemeStyles(currentTheme);
})();

// Initialize theme toggle when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeThemeToggle();
});

// Also try to initialize on window load as backup
window.addEventListener('load', function() {
    initializeThemeToggle();
});

// Manual theme toggle function for debugging
window.toggleTheme = function() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    applyThemeStyles(newTheme);
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.checked = newTheme === 'dark';
    }
    
    console.log('Manual theme toggle to:', newTheme);
}
