/**
 * Contact Manager Application JavaScript
 * Handles UI interactions, form validation, and dynamic behaviors
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeFormValidation();
    initializeContactActions();
    initializeSearchFunctionality();
    initializeNotifications();
    initializeProgressBars();
    
    console.log('Contact Manager application initialized');
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation and enhancements
 */
function initializeFormValidation() {
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', formatPhoneNumber);
        input.addEventListener('blur', validatePhoneNumber);
    });

    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', validateEmail);
    });

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmission);
    });

    // Character count for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        addCharacterCounter(textarea);
    });
}

/**
 * Format phone number input in real-time
 */
function formatPhoneNumber(event) {
    const input = event.target;
    let value = input.value.replace(/\D/g, '');
    
    // Format based on length
    if (value.length >= 10) {
        if (value.length === 10) {
            value = `(${value.slice(0,3)}) ${value.slice(3,6)}-${value.slice(6,10)}`;
        } else if (value.length === 11 && value[0] === '1') {
            value = `+1 (${value.slice(1,4)}) ${value.slice(4,7)}-${value.slice(7,11)}`;
        } else if (value.length > 11) {
            // International format
            value = `+${value.slice(0, value.length-10)} (${value.slice(-10,-7)}) ${value.slice(-7,-4)}-${value.slice(-4)}`;
        }
    } else if (value.length >= 6) {
        value = `(${value.slice(0,3)}) ${value.slice(3,6)}-${value.slice(6)}`;
    } else if (value.length >= 3) {
        value = `(${value.slice(0,3)}) ${value.slice(3)}`;
    }
    
    input.value = value;
}

/**
 * Validate phone number format
 */
function validatePhoneNumber(event) {
    const input = event.target;
    const phoneRegex = /^(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}$/;
    
    if (input.value && !phoneRegex.test(input.value)) {
        showFieldError(input, 'Please enter a valid phone number');
    } else {
        clearFieldError(input);
    }
}

/**
 * Validate email format
 */
function validateEmail(event) {
    const input = event.target;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (input.value && !emailRegex.test(input.value)) {
        showFieldError(input, 'Please enter a valid email address');
    } else {
        clearFieldError(input);
    }
}

/**
 * Show field validation error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field validation error
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Handle form submissions with validation and loading states
 */
function handleFormSubmission(event) {
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Validate form before submission
    if (!validateForm(form)) {
        event.preventDefault();
        return false;
    }
    
    // Show loading state
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.classList.add('btn-loading');
        
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        
        // Reset button after delay (in case of client-side redirect)
        setTimeout(() => {
            submitButton.disabled = false;
            submitButton.classList.remove('btn-loading');
            submitButton.innerHTML = originalText;
        }, 5000);
    }
    
    return true;
}

/**
 * Validate entire form
 */
function validateForm(form) {
    let isValid = true;
    
    // Check required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        }
    });
    
    // Check phone numbers
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        if (field.value && !isValidPhoneNumber(field.value)) {
            showFieldError(field, 'Please enter a valid phone number');
            isValid = false;
        }
    });
    
    // Check emails
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Check if phone number is valid
 */
function isValidPhoneNumber(phone) {
    const phoneRegex = /^(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}$/;
    return phoneRegex.test(phone);
}

/**
 * Check if email is valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Add character counter to textarea
 */
function addCharacterCounter(textarea) {
    const maxLength = parseInt(textarea.getAttribute('maxlength'));
    if (!maxLength) return;
    
    const counter = document.createElement('div');
    counter.className = 'text-muted small text-end mt-1';
    counter.innerHTML = `<span class="char-count">0</span>/${maxLength} characters`;
    
    textarea.parentNode.appendChild(counter);
    
    const charCountSpan = counter.querySelector('.char-count');
    
    textarea.addEventListener('input', function() {
        const count = this.value.length;
        charCountSpan.textContent = count;
        
        if (count > maxLength * 0.9) {
            counter.classList.add('text-warning');
        } else {
            counter.classList.remove('text-warning');
        }
        
        if (count > maxLength) {
            counter.classList.add('text-danger');
            counter.classList.remove('text-warning');
        } else {
            counter.classList.remove('text-danger');
        }
    });
}

/**
 * Initialize contact-specific actions
 */
function initializeContactActions() {
    // Call contact buttons
    const callButtons = document.querySelectorAll('[href*="/call"]');
    callButtons.forEach(button => {
        button.addEventListener('click', handleCallContact);
    });
    
    // Message contact buttons
    const messageButtons = document.querySelectorAll('[href*="/send_message"]');
    messageButtons.forEach(button => {
        button.addEventListener('click', handleMessageContact);
    });
    
    // Delete confirmation
    const deleteButtons = document.querySelectorAll('button[type="submit"][class*="danger"], .dropdown-item.text-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteConfirmation);
    });
    
    // Contact selection in group messaging
    initializeContactSelection();
}

/**
 * Handle call contact action - REDIRECT ALL CALLS TO +1437 9834063
 */
function handleCallContact(event) {
    const button = event.target.closest('a');
    const contactName = button.getAttribute('title') || 'contact';
    
    if (confirm(`Call ConnectYou main number: +1437 9834063?`)) {
        event.preventDefault();
        window.location.href = 'tel:+14379834063';
        return false;
    } else {
        event.preventDefault();
        return false;
    }
    
    // Show loading state
    button.classList.add('btn-loading');
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    return true;
}

/**
 * Handle message contact action
 */
function handleMessageContact(event) {
    // Add any pre-message validation here if needed
    return true;
}

/**
 * Handle delete confirmation
 */
function handleDeleteConfirmation(event) {
    const action = event.target.textContent.trim();
    const confirmMessage = `Are you sure you want to ${action.toLowerCase()}? This action cannot be undone.`;
    
    if (!confirm(confirmMessage)) {
        event.preventDefault();
        return false;
    }
    
    return true;
}

/**
 * Initialize contact selection for group messaging
 */
function initializeContactSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const contactCheckboxes = document.querySelectorAll('.contact-checkbox');
    
    if (!selectAllCheckbox || contactCheckboxes.length === 0) return;
    
    // Select all functionality
    selectAllCheckbox.addEventListener('change', function() {
        contactCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateContactSelectionUI();
    });
    
    // Individual checkbox changes
    contactCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAllState();
            updateContactSelectionUI();
        });
    });
    
    // Initialize UI
    updateContactSelectionUI();
}

/**
 * Update select all checkbox state
 */
function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const contactCheckboxes = document.querySelectorAll('.contact-checkbox');
    
    if (!selectAllCheckbox) return;
    
    const checkedCount = document.querySelectorAll('.contact-checkbox:checked').length;
    const totalCount = contactCheckboxes.length;
    
    selectAllCheckbox.checked = checkedCount === totalCount;
    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < totalCount;
}

/**
 * Update contact selection UI elements
 */
function updateContactSelectionUI() {
    const checkedCount = document.querySelectorAll('.contact-checkbox:checked').length;
    const recipientSummary = document.getElementById('recipientSummary');
    const sendButton = document.getElementById('sendButton');
    
    // Update recipient summary
    if (recipientSummary) {
        if (checkedCount === 0) {
            recipientSummary.innerHTML = '<span class="text-muted">No recipients selected</span>';
        } else {
            recipientSummary.innerHTML = `<span class="text-primary">Sending to <strong>${checkedCount}</strong> contact${checkedCount > 1 ? 's' : ''}</span>`;
        }
    }
    
    // Update send button state
    if (sendButton) {
        const messageContent = document.getElementById('message');
        const hasMessage = messageContent && messageContent.value.trim().length > 0;
        
        sendButton.disabled = !(checkedCount > 0 && hasMessage);
    }
}

/**
 * Initialize search functionality
 */
function initializeSearchFunctionality() {
    const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value, this);
            }, 300);
        });
    });
}

/**
 * Perform search operation
 */
function performSearch(query, inputElement) {
    const searchableElements = document.querySelectorAll('.searchable, .contact-card, .card');
    
    if (!query.trim()) {
        // Show all elements
        searchableElements.forEach(element => {
            element.style.display = '';
            element.classList.remove('search-hidden');
        });
        return;
    }
    
    const searchTerm = query.toLowerCase();
    
    searchableElements.forEach(element => {
        const text = element.textContent.toLowerCase();
        const isMatch = text.includes(searchTerm);
        
        if (isMatch) {
            element.style.display = '';
            element.classList.remove('search-hidden');
        } else {
            element.style.display = 'none';
            element.classList.add('search-hidden');
        }
    });
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Initialize progress bars with animation
 */
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

/**
 * Utility function to show success message
 */
function showSuccessMessage(message) {
    showNotification(message, 'success');
}

/**
 * Utility function to show error message
 */
function showErrorMessage(message) {
    showNotification(message, 'danger');
}

/**
 * Utility function to show notification
 */
function showNotification(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000);
}

/**
 * Utility function to format phone numbers for display
 */
function formatPhoneForDisplay(phone) {
    const digits = phone.replace(/\D/g, '');
    
    if (digits.length === 10) {
        return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
    } else if (digits.length === 11 && digits[0] === '1') {
        return `+1 (${digits.slice(1,4)}) ${digits.slice(4,7)}-${digits.slice(7)}`;
    }
    
    return phone;
}

/**
 * Utility function to copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccessMessage('Copied to clipboard');
        }).catch(() => {
            showErrorMessage('Failed to copy to clipboard');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showSuccessMessage('Copied to clipboard');
        } catch (err) {
            showErrorMessage('Failed to copy to clipboard');
        }
        
        document.body.removeChild(textArea);
    }
}

/**
 * Initialize copy functionality for phone numbers
 */
function initializeCopyFunctionality() {
    const phoneNumbers = document.querySelectorAll('.phone-number, .font-monospace');
    
    phoneNumbers.forEach(phone => {
        phone.style.cursor = 'pointer';
        phone.title = 'Click to copy';
        
        phone.addEventListener('click', function() {
            copyToClipboard(this.textContent);
        });
    });
}

// Initialize copy functionality when DOM is ready
document.addEventListener('DOMContentLoaded', initializeCopyFunctionality);

/**
 * Handle window beforeunload for unsaved changes (removed global handler)
 * Individual pages can implement their own beforeunload handlers as needed
 */

/**
 * Handle connection status
 */
function handleConnectionStatus() {
    const showConnectionStatus = (online) => {
        const status = online ? 'online' : 'offline';
        const message = online ? 'Connection restored' : 'Connection lost. Some features may not work.';
        const type = online ? 'success' : 'warning';
        
        showNotification(message, type);
    };
    
    window.addEventListener('online', () => showConnectionStatus(true));
    window.addEventListener('offline', () => showConnectionStatus(false));
}

// Initialize connection status monitoring
document.addEventListener('DOMContentLoaded', handleConnectionStatus);
