document.addEventListener('DOMContentLoaded', () => {

    // Get all elements
    const generateBtn = document.getElementById('generate-btn');
    const userInput = document.getElementById('user-input');
    const modelSelect = document.getElementById('model-select');
    const resultsOutput = document.getElementById('results-output');
    
    const refineSection = document.getElementById('refine-section');
    const refineInput = document.getElementById('refine-input');
    const refineBtn = document.getElementById('refine-btn');
    
    const copyBtn = document.getElementById('copy-btn');
    const saveHistoryBtn = document.getElementById('save-history-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Custom model elements
    const customModelInput = document.getElementById('custom-model-input');
    const customModelName = document.getElementById('custom-model-name');
    const searchModelBtn = document.getElementById('search-model-btn');
    const modelInfo = document.getElementById('model-info');

    const historyToggleBtn = document.getElementById('history-toggle-btn');
    const historyPanel = document.getElementById('history-panel');
    const historyCloseBtn = document.getElementById('history-close-btn');
    const historyList = document.getElementById('history-list');
    const historySearch = document.getElementById('history-search');
    const filterAllBtn = document.getElementById('filter-all');
    const filterFavoritesBtn = document.getElementById('filter-favorites');

    const darkModeToggle = document.getElementById('dark-mode-toggle');

    // Counter elements
    const charCount = document.getElementById('char-count');
    const wordCount = document.getElementById('word-count');
    const promptTokenCount = document.getElementById('prompt-token-count');
    const promptCharCount = document.getElementById('prompt-char-count');
    const promptWordCount = document.getElementById('prompt-word-count');

    // Template elements
    const templatesToggleBtn = document.getElementById('templates-toggle-btn');
    const templatesDropdown = document.getElementById('templates-dropdown');
    const templatesGrid = document.getElementById('templates-grid');
    const templateModal = document.getElementById('template-modal');
    const templateVariablesDiv = document.getElementById('template-variables');
    
    const templateModalTitle = document.getElementById('template-modal-title');
    const shortcutsBtn = document.getElementById('shortcuts-btn');
    const shortcutsModal = document.getElementById('shortcuts-modal');

    // Backend status elements
    const backendName = document.getElementById('backend-name');
    const backendIndicator = document.getElementById('backend-indicator');

    // Auth elements
    const authBtn = document.getElementById('auth-btn');
    const authBtnLabel = document.getElementById('auth-btn-label');
    const userDisplay = document.getElementById('user-display');
    const usernameSpan = document.getElementById('username-span');
    const authModal = document.getElementById('auth-modal');
    const authCloseBtn = document.getElementById('auth-close-btn');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const authForm = document.getElementById('auth-form');
    const authUsername = document.getElementById('auth-username');
    const authPassword = document.getElementById('auth-password');
    const authErrorMsg = document.getElementById('auth-error-msg');
    const authSubmitBtn = document.getElementById('auth-submit-btn');
    const authModalTitle = document.getElementById('auth-modal-title');

    // Store the last generated prompt for refinement
    let currentPrompt = "";
    let currentCustomModelId = "";
    let currentUserInput = "";
    let currentModel = "";
    let allTemplates = {};
    let currentTemplate = null;
    let isUserLoggedIn = false;
    let authMode = 'login'; // 'login' or 'register'

    /**
     * Debounce function for performance optimization
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} - Debounced function
     */
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

    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    function announceToScreenReader(message, priority = 'polite') {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', priority);
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            if (announcement.parentNode) {
                announcement.parentNode.removeChild(announcement);
            }
        }, 1000);
    }

    /**
     * Load and display backend configuration
     */
    async function loadBackendConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            const backendInfo = config.backends[config.backend];
            if (backendName && backendIndicator) {
                backendName.textContent = backendInfo.name;
                backendName.title = `URL: ${backendInfo.url}\nConfigured: ${backendInfo.configured ? 'Yes' : 'No'}`;
                
                // Set status indicator
                if (backendInfo.configured) {
                    backendIndicator.className = 'status-indicator unknown';
                    backendIndicator.title = 'Status unknown - click Generate to test';
                } else {
                    backendIndicator.className = 'status-indicator disconnected';
                    backendIndicator.title = 'Not configured';
                }
            }
        } catch (error) {
            console.error('Error loading backend config:', error);
            if (backendName) {
                backendName.textContent = 'Unknown';
            }
        }
    }

    /**
     * Estimate token count (rough approximation)
     */
    function estimateTokens(text) {
        if (!text) return 0;
        const chars = text.length;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
        // Average of character and word-based estimates
        return Math.round((chars / 4 + words / 0.75) / 2);
    }

    /**
     * Update input statistics
     */
    function updateInputStats() {
        if (!userInput) return;
        
        const text = userInput.value;
        const chars = text.length;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
        
        if (charCount) {
            const charValueSpan = charCount.querySelector('.stat-value');
            if (charValueSpan) {
                charValueSpan.textContent = chars;
            } else {
                charCount.textContent = `${chars} character${chars !== 1 ? 's' : ''}`;
            }
        }
        
        if (wordCount) {
            const wordValueSpan = wordCount.querySelector('.stat-value');
            if (wordValueSpan) {
                wordValueSpan.textContent = words;
            } else {
                wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
            }
        }
    }

    /**
     * Update prompt statistics
     */
    function updatePromptStats(text) {
        const chars = text.length;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
        const tokens = estimateTokens(text);
        
        if (promptCharCount) {
            promptCharCount.textContent = `${chars} character${chars !== 1 ? 's' : ''}`;
        }
        if (promptWordCount) {
            promptWordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
        }
        if (promptTokenCount) {
            promptTokenCount.textContent = `${tokens} tokens`;
            promptTokenCount.classList.remove('warning', 'danger');
            
            if (tokens > 4000) {
                promptTokenCount.classList.add('danger');
                promptTokenCount.title = 'Very long! May exceed model limits';
            } else if (tokens > 2000) {
                promptTokenCount.classList.add('warning');
                promptTokenCount.title = 'Long prompt - check model limits';
            } else {
                promptTokenCount.title = 'Estimated token count';
            }
        }
    }

    // Listen for input changes with debouncing for performance
    if (userInput) {
        userInput.addEventListener('input', debounce(updateInputStats, 100));
    }

    /**
     * Load templates
     */
    async function loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            if (!response.ok) throw new Error('Failed to load templates');
            
            allTemplates = await response.json();
            displayTemplates();
        } catch (error) {
            console.error('Error loading templates:', error);
            if (templatesGrid) {
                templatesGrid.innerHTML = '<p class="loading-text">Failed to load templates</p>';
            }
        }
    }

    /**
     * Escape HTML special characters to prevent XSS
     * @param {string} str - String to escape
     * @returns {string} - Escaped string
     */
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Display templates
     */
    function displayTemplates() {
        if (!templatesGrid) return;
        
        templatesGrid.innerHTML = Object.entries(allTemplates).map(([key, template]) => `
            <div class="template-card" role="listitem" tabindex="0" data-template-key="${escapeHtml(key)}">
                <div class="template-card-name">${escapeHtml(template.name)}</div>
                <div class="template-card-desc">${escapeHtml(template.description)}</div>
            </div>
        `).join('');
        
        // Use event delegation for template cards
        templatesGrid.querySelectorAll('.template-card').forEach(card => {
            const templateKey = card.dataset.templateKey;
            card.addEventListener('click', () => openTemplateModal(templateKey));
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openTemplateModal(templateKey);
                }
            });
        });
    }

    /**
     * Toggle templates dropdown
     */
    function toggleTemplates() {
        if (!templatesDropdown || !templatesToggleBtn) return;
        
        const isVisible = templatesDropdown.style.display === 'block';
        templatesDropdown.style.display = isVisible ? 'none' : 'block';
        templatesToggleBtn.setAttribute('aria-expanded', !isVisible);
        
        if (!isVisible && Object.keys(allTemplates).length === 0) {
            loadTemplates();
        }
    }

    /**
     * Open template modal
     */
    window.openTemplateModal = function(templateKey) {
        const template = allTemplates[templateKey];
        if (!template) return;
        
        currentTemplate = { key: templateKey, ...template };
        templateModalTitle.textContent = template.name;
        
        // Build variable inputs with proper accessibility
        templateVariablesDiv.innerHTML = Object.entries(template.variables).map(([varName, defaultValue]) => `
            <div class="template-variable">
                <label for="var-${varName}">${varName.replace(/_/g, ' ').toUpperCase()}:</label>
                <input type="text" id="var-${varName}" value="${defaultValue}" aria-label="${varName.replace(/_/g, ' ')}" />
            </div>
        `).join('');
        
        templateModal.style.display = 'flex';
        templateModal.setAttribute('aria-hidden', 'false');
        
        // Focus on first input for accessibility
        const firstInput = templateVariablesDiv.querySelector('input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    };

    /**
     * Close template modal
     */
    window.closeTemplateModal = function() {
        templateModal.style.display = 'none';
        templateModal.setAttribute('aria-hidden', 'true');
        currentTemplate = null;
        
        // Return focus to templates button
        if (templatesToggleBtn) {
            templatesToggleBtn.focus();
        }
    };

    /**
     * Show shortcuts modal
     */
    function showShortcutsModal() {
        if (!shortcutsModal) return;
        shortcutsModal.style.display = 'flex';
        shortcutsModal.setAttribute('aria-hidden', 'false');
        
        // Focus on modal for accessibility
        const closeBtn = shortcutsModal.querySelector('.close-btn');
        if (closeBtn) {
            setTimeout(() => closeBtn.focus(), 100);
        }
    }

    /**
     * Close shortcuts modal
     */
    window.closeShortcutsModal = function() {
        if (shortcutsModal) {
            shortcutsModal.style.display = 'none';
            shortcutsModal.setAttribute('aria-hidden', 'true');
            
            // Return focus to shortcuts button
            if (shortcutsBtn) {
                shortcutsBtn.focus();
            }
        }
    };

    /**
     * Apply template
     */
    window.applyTemplate = function() {
        if (!currentTemplate || !userInput) return;
        
        let text = currentTemplate.template;
        
        // Replace variables
        Object.keys(currentTemplate.variables).forEach(varName => {
            const input = document.getElementById(`var-${varName}`);
            if (input) {
                text = text.replace(`{${varName}}`, input.value);
            }
        });
        
        userInput.value = text;
        updateInputStats();
        closeTemplateModal();
        if (templatesDropdown) {
            templatesDropdown.style.display = 'none';
        }
        
        // Focus on input
        userInput.focus();
    };

    // Load templates on startup
    loadTemplates();
    
    // Load backend configuration on startup
    loadBackendConfig();
    
    if (templatesToggleBtn) {
        templatesToggleBtn.addEventListener('click', toggleTemplates);
    }
    if (shortcutsBtn) {
        shortcutsBtn.addEventListener('click', showShortcutsModal);
    }

    /**
     * Keyboard shortcuts
     */
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter: Generate prompt
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (document.activeElement === userInput && userInput.value.trim()) {
                handleGenerateClick();
            } else if (document.activeElement === refineInput && refineInput.value.trim()) {
                handleRefineClick();
            }
        }
        
        // Ctrl/Cmd + K: Toggle history
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleHistoryPanel();
        }
        
        // Ctrl/Cmd + D: Toggle dark mode
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            toggleDarkMode();
        }
        
        // Escape: Close modals/panels
        if (e.key === 'Escape') {
            if (historyPanel && historyPanel.classList.contains('open')) {
                historyPanel.classList.remove('open');
                historyPanel.setAttribute('aria-hidden', 'true');
                if (historyToggleBtn) {
                    historyToggleBtn.setAttribute('aria-expanded', 'false');
                    historyToggleBtn.focus();
                }
            }
            if (templateModal && templateModal.style.display === 'flex') {
                closeTemplateModal();
            }
            if (shortcutsModal && shortcutsModal.style.display === 'flex') {
                closeShortcutsModal();
            }
        }
    });

    /**
     * Detect platform and update shortcut display
     * Uses userAgentData (modern) with navigator.platform as fallback
     */
    function updateShortcutDisplay() {
        let isMac = false;
        
        // Modern approach: use userAgentData if available
        if (navigator.userAgentData && navigator.userAgentData.platform) {
            isMac = navigator.userAgentData.platform.toLowerCase().includes('mac');
        } else if (navigator.platform) {
            // Fallback to navigator.platform (deprecated but widely supported)
            isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        }
        
        document.querySelectorAll('.shortcut-ctrl').forEach(el => {
            el.style.display = isMac ? 'none' : 'inline';
        });
        document.querySelectorAll('.shortcut-cmd').forEach(el => {
            el.style.display = isMac ? 'inline' : 'none';
        });
        
        // Hide separator when one option is hidden (for screen readers)
        document.querySelectorAll('.shortcut-separator').forEach(el => {
            el.style.display = 'none';
        });
    }

    // Initialize platform-specific shortcuts
    updateShortcutDisplay();

    /**
     * Initialize dark mode from localStorage
     */
    function initDarkMode() {
        const darkMode = localStorage.getItem('darkMode') === 'true';
        if (darkMode && darkModeToggle) {
            document.body.classList.add('dark-mode');
            const iconSpan = darkModeToggle.querySelector('.icon');
            if (iconSpan) {
                iconSpan.textContent = '☀️';
            }
        }
    }

    /**
     * Toggle dark mode
     */
    function toggleDarkMode() {
        if (!darkModeToggle) return;
        
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', isDark);
        
        const iconSpan = darkModeToggle.querySelector('.icon');
        if (iconSpan) {
            iconSpan.textContent = isDark ? '☀️' : '🌙';
        }
    }

    // Initialize dark mode on load
    initDarkMode();

    /**
     * Shows or hides the loading spinner
     * @param {boolean} show - True to show, false to hide
     */
    function toggleLoading(show) {
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    /**
     * Handle model selection change
     */
    if (modelSelect) {
        modelSelect.addEventListener('change', () => {
            if (modelSelect.value === 'custom') {
                if (customModelInput) customModelInput.style.display = 'block';
            } else {
                if (customModelInput) customModelInput.style.display = 'none';
                if (modelInfo) modelInfo.style.display = 'none';
            }
        });
    }

    /**
     * Search for model best practices
     */
    async function handleSearchModel() {
        if (!customModelName || !modelInfo) return;
        
        const modelId = customModelName.value.trim();
        
        if (!modelId) {
            alert("Please enter a model ID");
            return;
        }

        toggleLoading(true);
        modelInfo.innerHTML = 'Searching for best practices...';
        modelInfo.style.display = 'block';

        try {
            const response = await fetch('/api/search-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            currentCustomModelId = data.model_id;
            
            let noteHtml = '';
            if (data.note) {
                noteHtml = `<p style="color: #856404; background: #fff3cd; padding: 8px; border-radius: 4px; margin-top: 8px;"><strong>⚠️ Note:</strong> ${data.note}</p>`;
            }
            
            modelInfo.innerHTML = `
                <h4>📋 Model: ${data.model_name || modelId}</h4>
                <p><strong>🎯 Preferred Format:</strong> ${data.preferred_format}</p>
                <p><strong>💡 Best Practices:</strong> ${data.best_practices || 'Use clear, structured instructions.'}</p>
                ${noteHtml}
            `;

        } catch (error) {
            console.error('Error:', error);
            modelInfo.innerHTML = `<p style="color: #d9534f;">❌ Failed to find information. Using generic format.</p>`;
            currentCustomModelId = modelId;
        } finally {
            toggleLoading(false);
        }
    }

    /**
     * Handles the 'Generate' button click
     */
    async function handleGenerateClick() {
        const userText = userInput.value;
        let selectedModel = modelSelect.value;
        let modelId = selectedModel;
        
        // Handle custom model
        if (selectedModel === 'custom') {
            const customModel = customModelName.value.trim();
            if (!customModel) {
                alert("Please enter a custom model ID or search for best practices first.");
                return;
            }
            modelId = customModel;
        }
        
        if (!userText) {
            alert("Please enter an idea first.");
            return;
        }

        toggleLoading(true);
        if (resultsOutput) resultsOutput.textContent = 'Generating...';
        if (copyBtn) copyBtn.disabled = true;
        if (refineSection) refineSection.style.display = 'none';

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_text: userText,
                    model: selectedModel,
                    custom_model_id: modelId !== selectedModel ? modelId : null
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            currentPrompt = data.generated_prompt; // Save for refinement
            currentUserInput = userText;
            currentModel = selectedModel;
            
            resultsOutput.textContent = currentPrompt;
            updatePromptStats(currentPrompt);
            
            if (copyBtn) copyBtn.disabled = false;
            if (saveHistoryBtn) saveHistoryBtn.disabled = false;
            
            if (refineSection) refineSection.style.display = 'block'; // Show the refine box
            
            // Update backend status to connected on success
            if (backendIndicator && currentPrompt && typeof currentPrompt === 'string' && !currentPrompt.startsWith('Error:')) {
                backendIndicator.className = 'status-indicator connected';
                backendIndicator.title = 'Connected and working';
            }
            
            // Announce to screen readers
            announceToScreenReader('Prompt generated successfully. You can now copy, save, analyze, or refine it.');

        } catch (error) {
            console.error('Error:', error);
            resultsOutput.textContent = `Failed to generate prompt. ${error.message}`;
            
            // Update backend status to disconnected on error
            if (backendIndicator) {
                backendIndicator.className = 'status-indicator disconnected';
                backendIndicator.title = `Connection error: ${error.message}`;
            }
            
            announceToScreenReader('Error generating prompt. Please check your connection and try again.', 'assertive');
        } finally {
            toggleLoading(false);
        }
    }

    /**
     * Handles the 'Refine' button click
     */
    async function handleRefineClick() {
        const feedback = refineInput.value;
        let selectedModel = modelSelect.value;
        let modelId = selectedModel;
        
        // Handle custom model
        if (selectedModel === 'custom') {
            const customModel = customModelName.value.trim() || currentCustomModelId;
            if (!customModel) {
                alert("Please enter a custom model ID.");
                return;
            }
            modelId = customModel;
        }

        if (!feedback) {
            alert("Please enter your refinement feedback.");
            return;
        }
        if (!currentPrompt) {
            alert("Please generate a prompt first.");
            return;
        }

        toggleLoading(true);
        resultsOutput.textContent = 'Refining...';

        try {
            const response = await fetch('/api/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    previous_prompt: currentPrompt,
                    feedback: feedback,
                    model: selectedModel,
                    custom_model_id: modelId !== selectedModel ? modelId : null
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Update with new prompt
            if (data.generated_prompt) {
                currentPrompt = data.generated_prompt;
                resultsOutput.textContent = currentPrompt;
                updatePromptStats(currentPrompt);
                refineInput.value = ""; // Clear feedback input
            } else {
                console.error('No generated_prompt in response:', data);
                resultsOutput.textContent = 'Error: No refined prompt received';
            }

        } catch (error) {
            console.error('Error:', error);
            resultsOutput.textContent = `Failed to refine prompt. ${error.message}`;
        } finally {
            toggleLoading(false);
        }
    }

    /**
     * Handles the 'Copy' button click
     */
    function handleCopyClick() {
        if (!currentPrompt || !copyBtn || copyBtn.disabled) return;

        navigator.clipboard.writeText(currentPrompt).then(() => {
            const originalHTML = copyBtn.innerHTML;
            copyBtn.innerHTML = '<span class="btn-icon" aria-hidden="true">✓</span> Copied!';
            announceToScreenReader('Prompt copied to clipboard');
            setTimeout(() => {
                copyBtn.innerHTML = originalHTML;
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            announceToScreenReader('Failed to copy prompt', 'assertive');
            alert('Failed to copy text.');
        });
    }

    /**
     * Save current prompt to history
     */
    async function handleSaveHistory() {
        if (!isUserLoggedIn) {
            openAuthModal('login');
            alert('Please log in to save prompts to history.');
            return;
        }
        if (!currentPrompt || !saveHistoryBtn) return;

        try {
            const response = await fetch('/api/history/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: currentPrompt,
                    model: currentModel,
                    user_input: currentUserInput
                })
            });

            if (response.status === 401) {
                setLoggedInState(false);
                openAuthModal('login');
                return;
            }
            if (!response.ok) throw new Error('Failed to save');

            const originalHTML = saveHistoryBtn.innerHTML;
            saveHistoryBtn.innerHTML = '<span class="btn-icon" aria-hidden="true">✓</span> Saved!';
            announceToScreenReader('Prompt saved to history');
            setTimeout(() => {
                saveHistoryBtn.innerHTML = originalHTML;
            }, 2000);

            // Refresh history if panel is open
            if (historyPanel && historyPanel.classList.contains('open')) {
                loadHistory();
            }
        } catch (error) {
            console.error('Error saving history:', error);
            announceToScreenReader('Failed to save to history', 'assertive');
            alert('Failed to save to history');
        }
    }

    async function loadHistory() {
        if (!isUserLoggedIn) {
            if (historyList) {
                historyList.innerHTML = '<p class="no-history" role="status">Please log in to view and save prompt history.</p>';
            }
            return;
        }
        if (!historySearch || !filterFavoritesBtn || !historyList) return;
        
        try {
            const search = historySearch.value;
            const favoritesOnly = filterFavoritesBtn.classList.contains('active');
            
            let url = '/api/history?';
            if (search) url += `search=${encodeURIComponent(search)}&`;
            if (favoritesOnly) url += 'favorites=true';

            const response = await fetch(url);
            if (response.status === 401) {
                setLoggedInState(false);
                return;
            }
            if (!response.ok) throw new Error('Failed to load history');

            const history = await response.json();
            displayHistory(history);
        } catch (error) {
            console.error('Error loading history:', error);
            if (historyList) {
                historyList.innerHTML = '<p class="no-history">Failed to load history</p>';
            }
        }
    }

    /**
     * Display history items
     */
    function displayHistory(history) {
        if (!historyList) return;
        
        if (history.length === 0) {
            historyList.innerHTML = '<p class="no-history" role="status">No prompts found</p>';
            return;
        }

        historyList.innerHTML = history.map(item => {
            // Validate ID is a number (no escaping needed for numbers)
            const itemId = Number(item.id);
            if (isNaN(itemId)) return '';
            
            return `
            <div class="history-item" data-id="${itemId}" role="listitem">
                <div class="history-item-header">
                    <span class="history-item-model">${escapeHtml(item.model)}</span>
                    <time class="history-item-time" datetime="${escapeHtml(item.timestamp)}">${escapeHtml(formatTime(item.timestamp))}</time>
                </div>
                ${item.user_input ? `<div class="history-item-input">"${escapeHtml(truncate(item.user_input, 100))}"</div>` : ''}
                <div class="history-item-prompt" tabindex="0" role="button" aria-label="Load this prompt" data-action="load">
                    ${escapeHtml(truncate(item.prompt, 200))}
                </div>
                <div class="history-item-actions" role="group" aria-label="Prompt actions">
                    <button class="history-action-btn favorite ${item.favorite ? 'active' : ''}" 
                            data-action="favorite"
                            aria-label="${item.favorite ? 'Remove from favorites' : 'Add to favorites'}"
                            aria-pressed="${item.favorite}">
                        ${item.favorite ? '⭐' : '☆'} Favorite
                    </button>
                    <button class="history-action-btn" data-action="copy" aria-label="Copy prompt to clipboard">
                        📋 Copy
                    </button>
                    <button class="history-action-btn delete" data-action="delete" aria-label="Delete this prompt">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
        }).join('');
        
        // Use event delegation for history items
        historyList.querySelectorAll('.history-item').forEach(item => {
            const id = parseInt(item.dataset.id, 10);
            
            // Load prompt handler
            const promptDiv = item.querySelector('[data-action="load"]');
            if (promptDiv) {
                promptDiv.addEventListener('click', () => loadHistoryPrompt(id));
                promptDiv.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        loadHistoryPrompt(id);
                    }
                });
            }
            
            // Favorite button handler
            const favoriteBtn = item.querySelector('[data-action="favorite"]');
            if (favoriteBtn) {
                favoriteBtn.addEventListener('click', () => toggleFavorite(id));
            }
            
            // Copy button handler
            const copyBtn = item.querySelector('[data-action="copy"]');
            if (copyBtn) {
                copyBtn.addEventListener('click', () => copyHistoryPrompt(id));
            }
            
            // Delete button handler
            const deleteBtn = item.querySelector('[data-action="delete"]');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => deleteHistoryItem(id));
            }
        });
        
        announceToScreenReader(`Loaded ${history.length} prompt${history.length !== 1 ? 's' : ''} from history`);
    }

    /**
     * Format timestamp
     */
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (hours < 1) return 'Just now';
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    /**
     * Truncate text
     */
    function truncate(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Load a history prompt into the results
     */
    window.loadHistoryPrompt = function(id) {
        fetch('/api/history')
            .then(r => r.json())
            .then(history => {
                const item = history.find(h => h.id === id);
                if (item) {
                    currentPrompt = item.prompt;
                    currentModel = item.model;
                    currentUserInput = item.user_input || '';
                    
                    if (resultsOutput) resultsOutput.textContent = item.prompt;
                    updatePromptStats(item.prompt);
                    
                    if (copyBtn) copyBtn.disabled = false;
                    if (saveHistoryBtn) saveHistoryBtn.disabled = false;
                    if (refineSection) refineSection.style.display = 'block';
                    
                    // Close history panel
                    historyPanel.classList.remove('open');
                    
                    // Scroll to results
                    resultsOutput.scrollIntoView({ behavior: 'smooth' });
                }
            });
    };

    /**
     * Copy history prompt
     */
    window.copyHistoryPrompt = function(id) {
        fetch('/api/history')
            .then(r => r.json())
            .then(history => {
                const item = history.find(h => h.id === id);
                if (item) {
                    navigator.clipboard.writeText(item.prompt).then(() => {
                        alert('Copied to clipboard!');
                    });
                }
            });
    };

    /**
     * Toggle favorite
     */
    window.toggleFavorite = async function(id) {
        try {
            const response = await fetch(`/api/history/${id}/favorite`, {
                method: 'POST'
            });
            if (response.status === 401) {
                setLoggedInState(false);
                openAuthModal('login');
                return;
            }
            if (!response.ok) throw new Error('Failed to toggle favorite');
            loadHistory();
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    };

    /**
     * Delete history item
     */
    window.deleteHistoryItem = async function(id) {
        if (!confirm('Delete this prompt from history?')) return;

        try {
            const response = await fetch(`/api/history/${id}`, {
                method: 'DELETE'
            });
            if (response.status === 401) {
                setLoggedInState(false);
                openAuthModal('login');
                return;
            }
            if (!response.ok) throw new Error('Failed to delete');
            loadHistory();
        } catch (error) {
            console.error('Error deleting history:', error);
        }
    };

    // Event listeners for history
    if (historyToggleBtn) {
        historyToggleBtn.addEventListener('click', toggleHistoryPanel);
    }
    if (historyCloseBtn && historyPanel) {
        historyCloseBtn.addEventListener('click', () => {
            historyPanel.classList.remove('open');
            historyPanel.setAttribute('aria-hidden', 'true');
            if (historyToggleBtn) {
                historyToggleBtn.setAttribute('aria-expanded', 'false');
                historyToggleBtn.focus();
            }
            announceToScreenReader('History panel closed');
        });
    }
    if (saveHistoryBtn) {
        saveHistoryBtn.addEventListener('click', handleSaveHistory);
    }
    if (historySearch) {
        // Debounce history search for performance
        historySearch.addEventListener('input', debounce(loadHistory, 300));
    }
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
    if (filterAllBtn && filterFavoritesBtn) {
        filterAllBtn.addEventListener('click', () => {
            filterAllBtn.classList.add('active');
            filterAllBtn.setAttribute('aria-pressed', 'true');
            filterFavoritesBtn.classList.remove('active');
            filterFavoritesBtn.setAttribute('aria-pressed', 'false');
            loadHistory();
        });
        
        filterFavoritesBtn.addEventListener('click', () => {
            filterFavoritesBtn.classList.add('active');
            filterFavoritesBtn.setAttribute('aria-pressed', 'true');
            filterAllBtn.classList.remove('active');
            filterAllBtn.setAttribute('aria-pressed', 'false');
            loadHistory();
        });
    }

    /**
     * Toggle history panel
     */
    function toggleHistoryPanel() {
        if (!historyPanel) return;
        const isOpen = historyPanel.classList.toggle('open');
        
        // Update ARIA attributes
        historyPanel.setAttribute('aria-hidden', !isOpen);
        if (historyToggleBtn) {
            historyToggleBtn.setAttribute('aria-expanded', isOpen);
        }
        
        if (isOpen) {
            historyPanel.style.display = 'flex';
            loadHistory();
            announceToScreenReader('History panel opened');
            
            // Focus on search for accessibility
            if (historySearch) {
                setTimeout(() => historySearch.focus(), 100);
            }
        } else {
            announceToScreenReader('History panel closed');
            
            // Return focus to toggle button
            if (historyToggleBtn) {
                historyToggleBtn.focus();
            }
        }
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerateClick);
    }
    if (refineBtn) {
        refineBtn.addEventListener('click', handleRefineClick);
    }
    if (copyBtn) {
        copyBtn.addEventListener('click', handleCopyClick);
    }
    if (searchModelBtn) {
        searchModelBtn.addEventListener('click', handleSearchModel);
    }
    
    // Template modal event listeners (replacing inline onclick handlers)
    const templateCloseBtn = document.getElementById('template-close-btn');
    const templateApplyBtn = document.getElementById('template-apply-btn');
    const templateCancelBtn = document.getElementById('template-cancel-btn');
    const shortcutsCloseBtn = document.getElementById('shortcuts-close-btn');
    
    if (templateCloseBtn) {
        templateCloseBtn.addEventListener('click', closeTemplateModal);
    }
    if (templateApplyBtn) {
        templateApplyBtn.addEventListener('click', applyTemplate);
    }
    if (templateCancelBtn) {
        templateCancelBtn.addEventListener('click', closeTemplateModal);
    }
    if (shortcutsCloseBtn) {
        shortcutsCloseBtn.addEventListener('click', closeShortcutsModal);
    }
});