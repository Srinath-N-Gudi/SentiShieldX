document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const refreshBtn = document.getElementById('refreshBtn');
    const groupsContainer = document.getElementById('groupsContainer');
    
    // Event Listeners
    refreshBtn.addEventListener('click', handleRefreshClick);
    
    // Main Functions
    async function handleRefreshClick() {
        const confirmed = await showConfirmationDialog(
            'Cosmic Group Scan',
            'This will check all groups and remove any where the bot is no longer a member. Continue?',
            'Scan Now',
            'Cancel'
        );
        
        if (confirmed) {
            await refreshGroups();
        }
    }
    
    async function refreshGroups() {
        try {
            // Show loading state
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning Cosmos...';
            
            // Make API request
            const response = await fetch('/refresh_groups', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            // Handle response
            if (!response.ok) {
                throw new Error(await response.text());
            }
            
            const data = await response.json();
            
            // Show appropriate feedback
            if (data.removed > 0) {
                showToast(
                    `Removed ${data.removed} inactive group${data.removed > 1 ? 's' : ''}`,
                    'warning',
                    5000
                );
            } else {
                showToast(
                    'Refresed Page!',
                    'success',
                    3000
                );
            }
            
            // Update UI
            renderGroups(data.groups);
            
        } catch (error) {
            console.error('Refresh error:', error);
            showToast(
                'Failed to refresh groups. Please try again.',
                'error',
                5000
            );
        } finally {
            // Reset button state
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Celestial Refresh';
        }
    }
    
    function renderGroups(groups) {
        if (groups.length === 0) {
            groupsContainer.innerHTML = `
                <div class="supernova-empty">
                    <div class="blackhole-icon"><i class="fas fa-comment-slash"></i></div>
                    <h2>The Void Whispers</h2>
                    <p>No sanctums found where your bot resides.</p>
                    <button class="nebula-button" onclick="window.open('https://t.me/SentiShield_Bot', '_blank')">
                        <i class="fas fa-paper-plane"></i> Summon to Group
                    </button>
                </div>
            `;
            return;
        }
        
        groupsContainer.innerHTML = groups.map(group => `
            <div class="singularity-card" onclick="window.location.href='/group_settings/${group.id}'">
                <div class="group-header">
                    <h3 class="group-name">${escapeHtml(group.name)}</h3>
                    <span class="group-type">
                        ${group.type === 'supergroup' ? 
                            '<i class="fas fa-users"></i> Supergroup' : 
                            group.type === 'channel' ? 
                            '<i class="fas fa-broadcast-tower"></i> Channel' : 
                            '<i class="fas fa-user-friends"></i> Group'}
                    </span>
                </div>
                <div class="group-divider"></div>
                <div class="group-meta">
                    <div class="meta-item">
                        <i class="fas fa-user-astronaut"></i>
                        <span>Added by YOU</span>
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-clock"></i>
                        <span>${formatDate(group.added)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    // Utility Functions
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    function formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString || 'Recently';
        }
    }
    
    // UI Components
    async function showConfirmationDialog(title, message, confirmText, cancelText) {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'cosmic-dialog-backdrop';
            dialog.innerHTML = `
                <div class="cosmic-dialog">
                    <h3>${title}</h3>
                    <p>${message}</p>
                    <div class="dialog-buttons">
                        <button class="nebula-button confirm">${confirmText}</button>
                        <button class="nebula-button cancel">${cancelText}</button>
                    </div>
                </div>
            `;
            
            const confirmBtn = dialog.querySelector('.confirm');
            const cancelBtn = dialog.querySelector('.cancel');
            
            confirmBtn.addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(true);
            });
            
            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(false);
            });
            
            document.body.appendChild(dialog);
        });
    }
    
    function showToast(message, type, duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `cosmic-toast ${type}`;
        toast.innerHTML = `
            <i class="fas ${getIconForType(type)}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, duration);
    }
    
    function getIconForType(type) {
        switch(type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }
    
    // Add CSS for dynamic elements
    const style = document.createElement('style');
    style.textContent = `
        .cosmic-dialog-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(2, 16, 29, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }
        
        .cosmic-dialog {
            background: linear-gradient(
                135deg,
                rgba(210, 123, 123, 0.15) 0%,
                rgba(2, 16, 29, 0.8) 100%
            );
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid var(--blood-rose);
            max-width: 500px;
            width: 90%;
            box-shadow: 0 10px 30px rgba(210, 123, 123, 0.3);
        }
        
        .cosmic-dialog h3 {
            color: var(--blood-rose);
            margin-top: 0;
            font-size: 1.5rem;
        }
        
        .cosmic-dialog p {
            margin: 1.5rem 0;
            line-height: 1.6;
        }
        
        .dialog-buttons {
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
        }
        
        .dialog-buttons button {
            padding: 0.8rem 1.5rem;
        }
        
        .dialog-buttons .cancel {
            background: transparent;
            border: 1px solid var(--blood-rose);
        }
        
        .cosmic-toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(
                135deg,
                rgba(210, 123, 123, 0.2) 0%,
                rgba(2, 16, 29, 0.9) 100%
            );
            padding: 1rem 2rem;
            border-radius: 50px;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 5px 20px rgba(210, 123, 123, 0.3);
            border: 1px solid var(--blood-rose);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }
        
        .cosmic-toast.success {
            border-color: var(--cosmic-teal);
        }
        
        .cosmic-toast.error {
            border-color: #ff4d4d;
        }
        
        .cosmic-toast.warning {
            border-color: #ffcc00;
        }
        
        .cosmic-toast i {
            font-size: 1.2rem;
        }
        
        .cosmic-toast.fade-out {
            animation: fadeOut 0.3s ease-in forwards;
        }
        
        @keyframes slideIn {
            from { transform: translateX(-50%) translateY(100px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
        
        @keyframes fadeOut {
            to { opacity: 0; transform: translateX(-50%) translateY(-50px); }
        }
    `;
    document.head.appendChild(style);
});