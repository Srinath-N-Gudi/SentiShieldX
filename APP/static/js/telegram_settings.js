document.addEventListener('DOMContentLoaded', function() {
    // Toast Notification System
    const Toast = {
        show: function(message, type = 'success', errors = null) {
            const toast = document.getElementById('toast');
            const icon = document.getElementById('toast-icon');
            const messageEl = document.getElementById('toast-message');
            
            toast.className = `toast toast-${type}`;
            icon.className = `fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}`;
            
            if (errors) {
                let errorList = '';
                for (const [field, message] of Object.entries(errors)) {
                    errorList += `${field}: ${message}\n`;
                }
                messageEl.innerHTML = `${message}<br><small>${errorList}</small>`;
            } else {
                messageEl.textContent = message;
            }
            
            toast.classList.remove('toast-hidden');
            
            setTimeout(() => {
                toast.classList.add('toast-hidden');
            }, errors ? 5000 : 3000);
        }
    };

    // Form Handler with Enhanced Validation
    const form = document.getElementById('settingsForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = document.getElementById('saveBtn');
            const originalBtnText = submitBtn.innerHTML;
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

            try {
                // Client-side validation
                const formData = new FormData(form);
                const validationErrors = {};
                
                if (!formData.get('muteDuration')?.trim()) {
                    validationErrors['muteDuration'] = 'Mute Duration is required';
                }
                if (!formData.get('warning_message')?.trim()) {
                    validationErrors['warning_message'] = 'Warning message is required';
                }
                if (!formData.get('repeat_offense_threshold')?.trim()) {
                    validationErrors['repeat_offense_threshold'] = 'Mute count is required';
                }
                if (!formData.get('admin_message')?.trim()) {
                    validationErrors['admin_message'] = 'Admin message is required';
                }
                
                if (Object.keys(validationErrors).length > 0) {
                    throw {
                        message: 'Validation failed',
                        errors: validationErrors
                    };
                }

                // Prepare data for server
                const jsonData = {
                    muteDuration: formData.get('muteDuration'),
                    warning_message: formData.get('warning_message'),
                    admin_message: formData.get('admin_message'),
                    repeat_offense_threshold: parseInt(formData.get('repeat_offense_threshold')),
                    repeat_action: formData.get('repeat_action'),
                    protection_enabled: formData.get('protection_enabled') === 'on',
                    allow_banning: formData.get('allow_banning') === 'on'
                };

                // Get CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
                
                // Send request
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(jsonData)
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw {
                        message: data.message || 'Failed to save settings',
                        errors: data.errors || null
                    };
                }

                Toast.show('Settings saved successfully!', 'success');
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
                
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }, 2000);

            } catch (error) {
                console.error('Error:', error);
                Toast.show(
                    error.message || 'An error occurred', 
                    'error', 
                    error.errors || null
                );
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Highlight invalid fields
                if (error.errors) {
                    for (const [field, message] of Object.entries(error.errors)) {
                        const input = form.querySelector(`[name="${field}"]`);
                        if (input) {
                            input.classList.add('invalid');
                            setTimeout(() => input.classList.remove('invalid'), 5000);
                        }
                    }
                }
            }
        });
    }
    // Preset message handlers
    document.querySelectorAll('.preset').forEach(preset => {
        preset.addEventListener('click', function() {
            document.querySelector('textarea[name="warning_message"]').value = this.textContent;
        });
    });

    // Placeholder handlers
    document.querySelectorAll('.placeholder').forEach(placeholder => {
        placeholder.addEventListener('click', function() {
            const textarea = document.querySelector('textarea[name="admin_message"]');
            textarea.value += this.textContent;
        });
    });

    // Add toast styles
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #1a1a2e;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease-out;
                border-left: 4px solid;
            }
            .toast-success {
                border-color: #4CAF50;
            }
            .toast-error {
                border-color: #f44336;
            }
            .toast i {
                font-size: 1.2em;
            }
            .toast-hidden {
                display: none;
            }
            @keyframes slideIn {
                from { bottom: -50px; opacity: 0; }
                to { bottom: 20px; opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
});