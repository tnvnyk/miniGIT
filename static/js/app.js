// Frontend JavaScript for MiniGitHub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFileUpload();
    initCodeHighlighting();
    initTooltips();
    initConfirmDialogs();
    initRepoSearch();
    initClipboard();
});

// File upload functionality
function initFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    
    if (!uploadArea || !fileInput) return;
    
    // Drag and drop events
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileList(files);
        }
    });
    
    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', function() {
        updateFileList(this.files);
    });
    
    // Form submission with progress
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = '<span class="spinner-border spinner-border-sm me-2"></span>';
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = spinner + 'Uploading...';
            }
        });
    }
}

// Update file list display
function updateFileList(files) {
    const fileList = document.getElementById('file-list');
    if (!fileList) return;
    
    fileList.innerHTML = '';
    
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'alert alert-info d-flex justify-content-between align-items-center';
        fileItem.innerHTML = `
            <div>
                <i class="fas fa-file me-2"></i>
                <span>${file.name}</span>
                <small class="text-muted ms-2">(${formatFileSize(file.size)})</small>
            </div>
        `;
        fileList.appendChild(fileItem);
    });
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Code syntax highlighting
function initCodeHighlighting() {
    // Auto-detect and highlight code blocks
    document.querySelectorAll('pre code').forEach(block => {
        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(block);
        }
    });
    
    // Add line numbers to code blocks
    document.querySelectorAll('.code-content pre').forEach(pre => {
        addLineNumbers(pre);
    });
}

// Add line numbers to code
function addLineNumbers(pre) {
    const lines = pre.textContent.split('\n');
    const lineNumbers = lines.map((_, i) => i + 1).join('\n');
    
    const lineNumbersEl = document.createElement('div');
    lineNumbersEl.className = 'line-numbers';
    lineNumbersEl.style.cssText = `
        position: absolute;
        left: 0;
        top: 0;
        padding: 16px 8px;
        background: rgba(0,0,0,0.1);
        color: #7d8590;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-size: 0.875rem;
        line-height: 1.45;
        text-align: right;
        min-width: 40px;
        user-select: none;
        border-right: 1px solid #21262d;
    `;
    lineNumbersEl.textContent = lineNumbers;
    
    pre.style.paddingLeft = '60px';
    pre.parentElement.style.position = 'relative';
    pre.parentElement.insertBefore(lineNumbersEl, pre);
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Confirmation dialogs
function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Repository search
function initRepoSearch() {
    const searchInput = document.getElementById('repo-search');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        const repoCards = document.querySelectorAll('.repo-card');
        
        repoCards.forEach(card => {
            const repoName = card.querySelector('.repo-name').textContent.toLowerCase();
            const repoDesc = card.querySelector('.repo-description')?.textContent.toLowerCase() || '';
            
            if (repoName.includes(query) || repoDesc.includes(query)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// Clipboard functionality
function initClipboard() {
    document.querySelectorAll('[data-clipboard]').forEach(element => {
        element.addEventListener('click', function() {
            const text = this.getAttribute('data-clipboard');
            copyToClipboard(text);
            
            // Show feedback
            const originalText = this.textContent;
            this.textContent = 'Copied!';
            this.classList.add('btn-success');
            
            setTimeout(() => {
                this.textContent = originalText;
                this.classList.remove('btn-success');
            }, 2000);
        });
    });
}

// Copy to clipboard helper
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

// Show flash messages
function showFlashMessage(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

// File tree navigation
function toggleFolder(element) {
    const folder = element.closest('.folder-item');
    const children = folder.querySelector('.folder-children');
    const icon = folder.querySelector('.folder-icon');
    
    if (children.style.display === 'none') {
        children.style.display = 'block';
        icon.className = 'folder-icon fas fa-folder-open';
    } else {
        children.style.display = 'none';
        icon.className = 'folder-icon fas fa-folder';
    }
}

// Auto-resize textareas
document.querySelectorAll('textarea[data-auto-resize]').forEach(textarea => {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
});

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Repository name validation
function validateRepoName(name) {
    const pattern = /^[a-zA-Z0-9._-]+$/;
    return pattern.test(name) && name.length > 0 && name.length <= 100;
}

// Commit message preview
function updateCommitPreview() {
    const messageInput = document.getElementById('commit-message');
    const preview = document.getElementById('commit-preview');
    
    if (messageInput && preview) {
        preview.textContent = messageInput.value || 'Add files via upload';
    }
}

// File size validation
function validateFileSize(files, maxSize = 10 * 1024 * 1024) { // 10MB default
    for (let file of files) {
        if (file.size > maxSize) {
            showFlashMessage(`File ${file.name} is too large. Maximum size is ${formatFileSize(maxSize)}.`, 'danger');
            return false;
        }
    }
    return true;
}

// Loading states
function showLoading(element, text = 'Loading...') {
    const spinner = '<span class="spinner-border spinner-border-sm me-2"></span>';
    element.innerHTML = spinner + text;
    element.disabled = true;
}

function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes} minutes ago`;
    if (hours < 24) return `${hours} hours ago`;
    if (days < 7) return `${days} days ago`;
    
    return date.toLocaleDateString();
}

// Export functions for global use
window.MiniGitHub = {
    showFlashMessage,
    validateForm,
    validateRepoName,
    formatFileSize,
    formatDate,
    copyToClipboard,
    toggleFolder,
    updateCommitPreview,
    validateFileSize
};