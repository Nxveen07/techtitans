document.addEventListener('DOMContentLoaded', () => {
    
    const viewContainer = document.getElementById('viewContainer');
    const navItems = document.querySelectorAll('.nav-item');
    // Use the same host that served the page so mobile devices on the same WiFi reach the backend
    const DEFAULT_API_BASE_URL = `http://${window.location.hostname}:8001`;
    let activeApiBaseUrl = DEFAULT_API_BASE_URL;
    let backendHeartbeatTimer = null;
    let backendIsConnected = false;

    function normalizeBaseUrl(url) {
        return String(url || '').trim().replace(/\/+$/, '');
    }

    function getApiCandidates() {
        const urlParams = new URLSearchParams(window.location.search);
        const fromQuery = urlParams.get('api');
        const fromStorage = window.localStorage.getItem('truthtrace_api_base');
        const host = window.location.hostname;
        const defaults = [`http://${host}:8001`, `http://${host}:8000`, 'http://127.0.0.1:8001', 'http://localhost:8001'];
        const merged = [fromQuery, fromStorage, ...defaults]
            .map(normalizeBaseUrl)
            .filter(Boolean);
        return [...new Set(merged)];
    }

    async function fetchWithTimeout(url, options = {}, timeoutMs = 1200) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        try {
            return await fetch(url, { ...options, signal: controller.signal });
        } finally {
            clearTimeout(timeoutId);
        }
    }

    async function findWorkingApiBase() {
        const candidates = getApiCandidates();
        const checks = candidates.map(async (base) => {
            const health = await fetchWithTimeout(`${base}/health`, { method: 'GET' });
            if (!health.ok) throw new Error('Health check failed');
            return base;
        });

        try {
            const winner = await Promise.any(checks);
            activeApiBaseUrl = winner;
            window.localStorage.setItem('truthtrace_api_base', winner);
            return winner;
        } catch (_) {
            activeApiBaseUrl = DEFAULT_API_BASE_URL;
            return null;
        }
    }

    async function refreshBackendStatusUI() {
        const backendStatus = document.getElementById('backendStatus');
        const btnAnalyze = document.getElementById('btnAnalyze');
        const workingBase = await findWorkingApiBase();

        if (workingBase) {
            if (backendStatus) backendStatus.textContent = `Backend status: connected \u2713 (${workingBase})`;
            if (btnAnalyze) btnAnalyze.disabled = false;
            backendIsConnected = true;
            return true;
        }

        if (backendStatus) backendStatus.textContent = 'Backend status: disconnected — retrying automatically...';
        if (btnAnalyze) btnAnalyze.disabled = true;
        backendIsConnected = false;
        return false;
    }

    function startBackendHeartbeat() {
        if (backendHeartbeatTimer) return;
        const tick = async () => {
            await refreshBackendStatusUI();
            const nextDelayMs = backendIsConnected ? 8000 : 1500;
            backendHeartbeatTimer = window.setTimeout(tick, nextDelayMs);
        };
        tick();
    }

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            refreshBackendStatusUI();
        }
    });
    
    // Theme Toggling Logic
    const themeToggle = document.getElementById('themeToggle');
    const htmlEl = document.documentElement;
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');

    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlEl.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlEl.setAttribute('data-theme', newTheme);
        
        if (newTheme === 'dark') {
            moonIcon.classList.add('active');
            sunIcon.classList.remove('active');
        } else {
            sunIcon.classList.add('active');
            moonIcon.classList.remove('active');
        }
    });

    // View Routing Logic
    function getFriendlyErrorMessage(detail) {
        const text = String(detail || '').toLowerCase();
        if (text.includes('quota exceeded') || text.includes('resource_exhausted') || text.includes('429')) {
            return 'Gemini quota is exhausted. Wait for reset or use a different API key/project.';
        }
        if (text.includes('missing') && text.includes('gemini_api_key')) {
            return 'Gemini API key is missing. Add it in backend/.env and restart backend.';
        }
        if (text.includes('not enough text context')) {
            return 'Please provide a longer claim or a valid URL.';
        }
        return detail || 'Backend error. Please try again.';
    }

    function loadView(viewId, data = null, isInitialLoad = false) {
        const templateId = `view-${viewId}`;
        const template = document.getElementById(templateId);
        
        if (template) {
            if (isInitialLoad) {
                // Instantly load without fade-out for the first render
                viewContainer.innerHTML = '';
                const node = template.content.cloneNode(true);
                viewContainer.appendChild(node);
                viewContainer.style.opacity = 1;
                setupViewSpecificEvents(viewId, data);
            } else {
                // Fade out current content
                viewContainer.style.opacity = 0;
                
                setTimeout(() => {
                    viewContainer.innerHTML = '';
                    const node = template.content.cloneNode(true);
                    viewContainer.appendChild(node);
                    
                    // Force a reflow so the browser registers the opacity change properly
                    void viewContainer.offsetWidth; 
                    
                    viewContainer.style.opacity = 1;
                    
                    // Set up event listeners for newly injected elements
                    setupViewSpecificEvents(viewId, data);
                }, 200); // Wait for the 0.2s CSS transition to finish before swapping
            }
        }
    }

    async function setupViewSpecificEvents(viewId, data = null) {
        if (viewId === 'dashboard') {
            const btnAnalyze = document.getElementById('btnAnalyze');
            const mainInput = document.getElementById('mainInput');
            startBackendHeartbeat();

            if(btnAnalyze) {
                btnAnalyze.addEventListener('click', async () => {
                    const val = mainInput.value;
                    if(val.trim() === '') {
                        alert("Please enter a link or text to analyze.");
                        return;
                    }
                    
                    btnAnalyze.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Analyzing via TruthTrace Backend...';
                    
                    try {
                        const connectedBase = (await findWorkingApiBase()) || activeApiBaseUrl;
                        const response = await fetch(`${connectedBase}/api/v1/content/analyze`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ content: val, type: 'url' })
                        });
                        const result = await response.json();
                        if(!response.ok) {
                            const detail = result?.detail || "Backend error";
                            throw new Error(getFriendlyErrorMessage(detail));
                        }
                        
                        // Switch nav active state to analysis
                        updateNavState('analysis');
                        loadView('analysis', result.analysis);
                    } catch (e) {
                         console.error(e);
                         alert(`Analysis failed: ${e.message}`);
                         btnAnalyze.innerHTML = 'Analyze with AI';
                    }
                });
            }
        } else if (viewId === 'analysis' && data) {
            // Populate DOM with backend response
            const scoreEl = document.querySelector('.percentage');
            const statusBadge = document.querySelector('.status-badge');
            const explanationEl = document.querySelector('.ai-explanation');
            const circularChart = document.querySelector('.circular-chart');
            const credibilityRow = document.getElementById('credibilityRow');
            const credibilityScore = document.getElementById('credibilityScore');
            const crossVerifyBox = document.getElementById('crossVerifyBox');
            const crossVerifyLinks = document.getElementById('crossVerifyLinks');
            const factEngineRow = document.getElementById('factEngineRow');
            const factEngineBadge = document.getElementById('factEngineBadge');
            
            if (scoreEl) scoreEl.textContent = `${data.fake_probability}%`;

            if (credibilityRow && credibilityScore && typeof data.credibility_score === 'number') {
                credibilityScore.textContent = String(data.credibility_score);
                credibilityRow.style.display = 'block';
            } else if (credibilityRow) {
                credibilityRow.style.display = 'none';
            }

            if (factEngineRow && factEngineBadge) {
                const provider = String(data.fact_check_provider || '').toLowerCase();
                if (provider) {
                    const isGroq = provider === 'groq';
                    factEngineBadge.textContent = isGroq ? 'Groq' : 'Fallback';
                    factEngineBadge.classList.remove('success', 'warning');
                    factEngineBadge.classList.add(isGroq ? 'success' : 'warning');
                    factEngineRow.style.display = 'block';
                } else {
                    factEngineBadge.textContent = 'Fallback';
                    factEngineBadge.classList.remove('success');
                    factEngineBadge.classList.add('warning');
                    factEngineRow.style.display = 'block';
                }
            }
            
            if (statusBadge) {
                statusBadge.textContent = data.classification;
                if (data.classification === 'Verified Fact') {
                    statusBadge.classList.replace('fake', 'success');
                    if(circularChart) circularChart.classList.remove('fake');
                } else {
                    statusBadge.classList.add('fake');
                    statusBadge.classList.remove('success');
                    if(circularChart) circularChart.classList.add('fake');
                }
            }
            
            if (explanationEl) {
                explanationEl.innerHTML = `<i class="ph ph-robot"></i> <strong>AI Assistant:</strong> ${data.explanation}`;
            }
            
            const analysisClaim = document.getElementById('analysisClaim');
            const analysisFact = document.getElementById('analysisFact');
            const analysisSource = document.getElementById('analysisSource');
            
            if (analysisClaim && data.claim) analysisClaim.textContent = data.claim;
            if (analysisFact && data.fact) analysisFact.textContent = data.fact;
            if (analysisSource && data.source) analysisSource.textContent = data.source;

            // Cross-verification evidence links (best-effort)
            if (crossVerifyBox && crossVerifyLinks && data.cross_verification && Array.isArray(data.cross_verification.evidence)) {
                const links = data.cross_verification.evidence.slice(0, 4);
                crossVerifyLinks.innerHTML = links.map((e) => {
                    const title = (e && e.title) ? e.title : 'Source';
                    const url = (e && e.url) ? e.url : '#';
                    const domain = (e && e.domain) ? ` (${e.domain})` : '';
                    return `<div><a class="source-link" href="${url}" target="_blank" rel="noopener noreferrer">${title}${domain}</a></div>`;
                }).join('');
                crossVerifyBox.style.display = links.length ? 'block' : 'none';
            } else if (crossVerifyBox) {
                crossVerifyBox.style.display = 'none';
            }
        }
    }

    function updateNavState(targetId) {
        navItems.forEach(item => {
            if(item.getAttribute('data-target') === targetId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // Navigation Click Events
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active from all
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active to clicked
            item.classList.add('active');
            
            const target = item.getAttribute('data-target');
            loadView(target);
        });
    });

    // Mobile menu generic toggle (mock)
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    if(mobileBtn) {
        mobileBtn.addEventListener('click', () => {
            // In a full implementation, this opens a side drawer.
            alert("Mobile menu clicked!");
        });
    }

    // Load default view (dashboard)
    viewContainer.style.transition = 'opacity 0.2s ease-in-out';
    loadView('dashboard', null, true);
});
