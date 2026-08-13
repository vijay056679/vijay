/* -------------------------------------------------------------
   AI College Enquiry System - Frontend SPA Controller (app.js)
   ------------------------------------------------------------- */

const API_BASE = 'http://127.0.0.1:5000';
let charts = {};
let currentTab = 'dashboard';
let selectedUnansweredId = null;
let systemStats = { total_users: 0, total_queries: 0, accuracy_rate: 0, pending_questions: 0 };
let unansweredQueries = [];
let botUsers = [];
let kbItems = [];
let isServerOnline = false;

// Voice Speech APIs
let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
}

// ----------------- Initialization -----------------

let currentUser = null; // Stores logged-in student user data object
let currentUserTab = 'user-dashboard';

document.addEventListener('DOMContentLoaded', async () => {
    if (window.partialsReady) {
        try {
            await window.partialsReady;
        } catch (error) {
            console.error('Failed to load page partials', error);
            return;
        }
    }

    initApp();
    setupEventListeners();
    setupLandingEventListeners();
    setupUserEventListeners();
    checkServerConnection();
    loadApplicationState();
    
    // Poll server status every 10 seconds
    setInterval(checkServerConnection, 10000);
});

function initApp() {
    lucide.createIcons();
    initCharts();
}

// ----------------- Authentication & State Routing -----------------

function loadApplicationState() {
    const adminToken = localStorage.getItem('adminToken');
    const userTokenStr = localStorage.getItem('userToken');
    
    const landingContainer = document.getElementById('landing-container');
    const adminContainer = document.getElementById('admin-container');
    const userContainer = document.getElementById('user-container');
    
    // Hide all portal interfaces initially
    landingContainer.classList.add('hidden');
    adminContainer.classList.add('hidden');
    userContainer.classList.add('hidden');
    
    if (adminToken === 'admin-mock-session-token') {
        adminContainer.classList.remove('hidden');
        switchTab('dashboard');
    } else if (userTokenStr) {
        try {
            currentUser = JSON.parse(userTokenStr);
            userContainer.classList.remove('hidden');
            
            // Populate student sidebar
            document.getElementById('user-name-display').textContent = currentUser.name;
            document.getElementById('user-id-display').textContent = currentUser.user_id;
            document.getElementById('user-avatar-display').src = `https://api.dicebear.com/7.x/initials/svg?seed=${currentUser.name}`;
            
            switchUserTab('user-dashboard');
        } catch (e) {
            console.error("Failed to parse user profile token", e);
            localStorage.removeItem('userToken');
            showLandingPage();
        }
    } else {
        showLandingPage();
    }
}

function showLandingPage() {
    const landingContainer = document.getElementById('landing-container');
    landingContainer.classList.remove('hidden');
    switchLandingView('landing-home');
}

function switchLandingView(viewId) {
    document.querySelectorAll('.landing-view').forEach(view => {
        view.classList.remove('active');
        view.classList.add('hidden');
    });
    
    const activeView = document.getElementById(`${viewId}-view`);
    if (activeView) {
        activeView.classList.remove('hidden');
        activeView.classList.add('active');
    }
}

function setupLandingEventListeners() {
    const studentPortalBtn = document.getElementById('open-student-login');
    const adminPortalBtn = document.getElementById('open-admin-login');

    if (studentPortalBtn) {
        studentPortalBtn.addEventListener('click', () => {
            window.location.href = 'login.html';
        });
    }

    if (adminPortalBtn) {
        adminPortalBtn.addEventListener('click', () => {
            window.location.href = 'admin_login.html';
        });
    }

    // Back links return to the portal selection.
    document.querySelectorAll('.back-to-portal').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            switchLandingView('landing-home');
        });
    });
    
    // Toggle registration links if elements exist
    const linkToReg = document.getElementById('link-to-register');
    if (linkToReg) {
        linkToReg.addEventListener('click', (e) => {
            e.preventDefault();
            switchLandingView('student-register');
        });
    }
    
    const linkToLogin = document.getElementById('link-to-login');
    if (linkToLogin) {
        linkToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            switchLandingView('student-login');
        });
    }
    
    // Form submissions if elements exist
    const studentLoginForm = document.getElementById('student-login-form');
    if (studentLoginForm) {
        studentLoginForm.addEventListener('submit', handleStudentLogin);
    }
    
    const studentRegisterForm = document.getElementById('student-register-form');
    if (studentRegisterForm) {
        studentRegisterForm.addEventListener('submit', handleStudentRegister);
    }

    const adminLoginForm = document.getElementById('admin-login-form');
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', handleAdminLogin);
    }
}

async function handleStudentLogin(e) {
    e.preventDefault();
    const emailEl = document.getElementById('student-login-email');
    const passEl = document.getElementById('student-login-password');
    const errEl = document.getElementById('student-login-error');
    
    const email = emailEl.value.trim();
    const password = passEl.value.trim();
    
    errEl.classList.add('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/api/user/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        
        if (res.ok && data.success) {
            localStorage.setItem('userToken', JSON.stringify(data.user));
            emailEl.value = '';
            passEl.value = '';
            showSuccessNotification(`Welcome back, ${data.user.name}!`);
            loadApplicationState();
        } else {
            errEl.textContent = data.error || 'Invalid credentials';
            errEl.classList.remove('hidden');
        }
    } catch (err) {
        errEl.textContent = 'Connection error. Make sure Python backend is running.';
        errEl.classList.remove('hidden');
    }
}

async function handleStudentRegister(e) {
    e.preventDefault();
    const nameEl = document.getElementById('student-reg-name');
    const emailEl = document.getElementById('student-reg-email');
    const passEl = document.getElementById('student-reg-password');
    const errEl = document.getElementById('student-reg-error');
    
    const name = nameEl.value.trim();
    const email = emailEl.value.trim();
    const password = passEl.value.trim();
    
    errEl.classList.add('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, platform: 'Web Portal' })
        });
        
        const data = await res.json();
        
        if (res.ok && data.success) {
            showSuccessNotification('Account created successfully! Please login.');
            document.getElementById('student-login-email').value = email;
            nameEl.value = '';
            emailEl.value = '';
            passEl.value = '';
            switchLandingView('student-login');
        } else {
            errEl.textContent = data.error || 'Registration failed';
            errEl.classList.remove('hidden');
        }
    } catch (err) {
        errEl.textContent = 'Connection error. Make sure Python backend is running.';
        errEl.classList.remove('hidden');
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    const userEl = document.getElementById('admin-login-username');
    const passEl = document.getElementById('admin-login-password');
    const errEl = document.getElementById('admin-login-error');
    
    const username = userEl.value.trim();
    const password = passEl.value.trim();
    
    errEl.classList.add('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await res.json();
        
        if (res.ok && data.success) {
            localStorage.setItem('adminToken', data.token);
            userEl.value = '';
            passEl.value = '';
            showSuccessNotification('Authenticated successfully as Administrator');
            loadApplicationState();
        } else {
            errEl.textContent = data.error || 'Invalid credentials';
            errEl.classList.remove('hidden');
        }
    } catch (err) {
        errEl.textContent = 'Server connection error. Make sure Python Flask is running.';
        errEl.classList.remove('hidden');
    }
}

function handleStudentLogout() {
    if (confirm('Are you sure you want to log out?')) {
        localStorage.removeItem('userToken');
        currentUser = null;
        window.location.href = 'login.html';
    }
}

function handleAdminLogout() {
    if (confirm('Are you sure you want to log out of the Admin panel?')) {
        localStorage.removeItem('adminToken');
        window.location.href = 'admin_login.html';
    }
}

// ----------------- Navigation & Theme -----------------

function setupEventListeners() {
    // Logout Action via Operator Profile click
    const operatorProfile = document.getElementById('admin-profile-header');
    if (operatorProfile) {
        operatorProfile.addEventListener('click', handleAdminLogout);
        operatorProfile.style.cursor = 'pointer';
        operatorProfile.title = 'Click to Log Out';
    }

    const adminLogoutBtn = document.getElementById('admin-logout-btn');
    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener('click', handleAdminLogout);
    }

    // Sidebar Tabs
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
            document.getElementById('sidebar').classList.remove('open');
        });
    });

    // Mobile Sidebar Toggle
    document.getElementById('mobile-toggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.add('open');
    });
    
    // Tap outside mobile sidebar to close
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('mobile-toggle');
        if (window.innerWidth <= 768 && 
            sidebar && toggle &&
            !sidebar.contains(e.target) && 
            !toggle.contains(e.target) && 
            sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });

    // Theme Switcher
    document.getElementById('theme-toggle').addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
    });

    // Refresh Button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.classList.add('rotating');
        setTimeout(() => refreshBtn.classList.remove('rotating'), 800);
        refreshData();
    });

    // Notification Panel Toggle
    const notiBtn = document.getElementById('notification-btn');
    const notiDropdown = document.getElementById('notification-dropdown');
    if (notiBtn && notiDropdown) {
        notiBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notiDropdown.classList.toggle('open');
        });

        document.addEventListener('click', (e) => {
            if (!notiDropdown.contains(e.target) && !notiBtn.contains(e.target)) {
                notiDropdown.classList.remove('open');
            }
        });
    }

    const clearNotiBtn = document.getElementById('clear-noti');
    if (clearNotiBtn) {
        clearNotiBtn.addEventListener('click', () => {
            document.getElementById('noti-list').innerHTML = '<div class="noti-empty">No new activities</div>';
            document.getElementById('noti-dot').classList.remove('active');
        });
    }

    // Unanswered Queue selections
    document.getElementById('resolve-form').addEventListener('submit', submitResolveAnswer);

    // Filter Listeners in User registry
    document.getElementById('user-search-input').addEventListener('input', renderUsersList);
    document.getElementById('user-status-filter').addEventListener('change', renderUsersList);

    // Knowledge Base manager CRUD triggers
    document.getElementById('add-kb-btn').addEventListener('click', openAddKBModal);
    document.getElementById('kb-modal-close').addEventListener('click', () => {
        document.getElementById('kb-modal').classList.remove('open');
    });
    document.getElementById('kb-form').addEventListener('submit', submitKBForm);
    document.getElementById('kb-search-input').addEventListener('input', renderKBList);
    document.getElementById('kb-category-filter').addEventListener('change', renderKBList);

    // Notice Manager triggers
    const addNoticeBtn = document.getElementById('add-notice-btn');
    const noticeModal = document.getElementById('notice-modal');
    const noticeModalClose = document.getElementById('notice-modal-close');
    const noticeForm = document.getElementById('notice-form');
    
    if (addNoticeBtn) {
        addNoticeBtn.addEventListener('click', () => {
            noticeModal.classList.add('open');
            document.getElementById('notice-title').focus();
        });
    }
    if (noticeModalClose) {
        noticeModalClose.addEventListener('click', () => {
            noticeModal.classList.remove('open');
        });
    }
    if (noticeForm) {
        noticeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('notice-title').value.trim();
            const content = document.getElementById('notice-content').value.trim();
            
            try {
                const res = await fetch(`${API_BASE}/api/notices`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
                });
                if (res.ok) {
                    showSuccessNotification("Notice published successfully!");
                    noticeModal.classList.remove('open');
                    noticeForm.reset();
                    loadAdminNotices();
                } else {
                    alert("Failed to publish announcement notice.");
                }
            } catch (err) {
                console.error(err);
                alert("Server connection error during notice publication.");
            }
        });
    }

    const noticesSearch = document.getElementById('admin-notices-search');
    if (noticesSearch) {
        noticesSearch.addEventListener('input', loadAdminNotices);
    }
    
    const feedbackSearch = document.getElementById('admin-feedback-search');
    if (feedbackSearch) {
        feedbackSearch.addEventListener('input', loadAdminFeedback);
    }

    // Modal Close buttons
    document.getElementById('modal-close').addEventListener('click', () => {
        document.getElementById('user-modal').classList.remove('open');
    });
    
    document.getElementById('user-modal').addEventListener('click', (e) => {
        if (e.target.id === 'user-modal') {
            document.getElementById('user-modal').classList.remove('open');
        }
    });

    // Close suggestions box on click outside or escape key
    document.addEventListener('click', (e) => {
        const suggestionsBox = document.getElementById('search-suggestions');
        const input = document.getElementById('chat-input');
        if (suggestionsBox && input && !suggestionsBox.contains(e.target) && e.target !== input) {
            suggestionsBox.classList.add('hidden');
        }
        
        const userSuggestionsBox = document.getElementById('user-search-suggestions');
        const userInput = document.getElementById('user-chat-input');
        if (userSuggestionsBox && userInput && !userSuggestionsBox.contains(e.target) && e.target !== userInput) {
            userSuggestionsBox.classList.add('hidden');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const suggestionsBox = document.getElementById('search-suggestions');
            if (suggestionsBox) suggestionsBox.classList.add('hidden');
            
            const userSuggestionsBox = document.getElementById('user-search-suggestions');
            if (userSuggestionsBox) userSuggestionsBox.classList.add('hidden');
            
            const kbModal = document.getElementById('kb-modal');
            if (kbModal) kbModal.classList.remove('open');
            
            const userCreateModal = document.getElementById('user-create-modal');
            if (userCreateModal) userCreateModal.classList.remove('open');
            
            const userModal = document.getElementById('user-modal');
            if (userModal) userModal.classList.remove('open');
            
            const noticeModal = document.getElementById('notice-modal');
            if (noticeModal) noticeModal.classList.remove('open');
        }
    });

    // CSV Reports Export buttons bindings
    const bindOptionalClick = (id, handler) => {
        const element = document.getElementById(id);
        if (element) element.addEventListener('click', handler);
    };

    bindOptionalClick('export-queries-btn', () => {
        window.location.href = `${API_BASE}/api/export/queries`;
    });
    bindOptionalClick('export-users-btn', () => {
        window.location.href = `${API_BASE}/api/export/users`;
    });
    bindOptionalClick('export-faq-btn', () => {
        window.location.href = `${API_BASE}/api/export/faq`;
    });
    bindOptionalClick('export-pdf-btn', () => {
        window.print();
    });
}

function switchTab(tabId) {
    currentTab = tabId;
    
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    document.querySelectorAll('#admin-container .view-section').forEach(view => {
        const id = view.getAttribute('id');
        if (id === `view-${tabId}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    const titleMap = {
        'dashboard': 'Operations Dashboard',
        'unanswered': 'Unanswered Query Queue',
        'bot-users': 'Bot User Registry',
        'kb-manager': 'Knowledge Base CRUD Management',
        'admin-notices': 'Notice Board Manager',
        'admin-feedback': 'General Student Feedback'
    };
    document.getElementById('page-title').textContent = titleMap[tabId] || 'Dept. CsBot Operations';
    
    refreshData();
}

// ----------------- API Integration & Status -----------------

async function checkServerConnection() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) {
            isServerOnline = true;
            updateStatusUI(true);
        } else {
            throw new Error();
        }
    } catch (err) {
        isServerOnline = false;
        updateStatusUI(false);
    }
}

function updateStatusUI(online) {
    return;
}

function refreshData() {
    if (!isServerOnline) return;
    
    if (currentTab === 'dashboard') {
        loadDashboardStats();
    } else if (currentTab === 'unanswered') {
        loadUnansweredQueue();
    } else if (currentTab === 'bot-users') {
        loadBotUsers();
    } else if (currentTab === 'kb-manager') {
        loadKnowledgeBase();
    } else if (currentTab === 'admin-notices') {
        loadAdminNotices();
    } else if (currentTab === 'admin-feedback') {
        loadAdminFeedback();
    }
    
    loadUnansweredBadgeCount();
}

async function loadUnansweredBadgeCount() {
    try {
        const res = await fetch(`${API_BASE}/api/unanswered`);
        if (res.ok) {
            const data = await res.json();
            const count = data.length;
            const badge = document.getElementById('unanswered-badge');
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
            
            const kpiCard = document.getElementById('kpi-pending-card');
            if (kpiCard) {
                if (count > 0) {
                    kpiCard.classList.add('active');
                } else {
                    kpiCard.classList.remove('active');
                }
            }
        }
    } catch (err) {
        console.error('Error fetching unanswered badge count', err);
    }
}

// ----------------- Dashboard tab -----------------

async function loadDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (!res.ok) return;
        
        systemStats = await res.json();
        
        document.getElementById('stat-total-users').textContent = systemStats.total_users;
        document.getElementById('stat-total-queries').textContent = systemStats.total_queries;
        const accuracyStat = document.getElementById('stat-accuracy-rate');
        if (accuracyStat) accuracyStat.textContent = `${systemStats.accuracy_rate}%`;
        document.getElementById('stat-pending-questions').textContent = systemStats.pending_questions;
        document.getElementById('stat-pending-subtext').textContent = 
            systemStats.pending_questions > 0 ? `${systemStats.pending_questions} queries need training` : 'System fully trained';
            
        renderActivities(systemStats.activities);
        renderTopQueries(systemStats.top_queries);
        updateChartsData();
        
    } catch (err) {
        console.error('Error loading dashboard statistics', err);
    }
}

function renderActivities(activities) {
    const list = document.getElementById('dashboard-activities');
    const notiList = document.getElementById('noti-list');
    const notiDot = document.getElementById('noti-dot');
    
    if (!activities || activities.length === 0) {
        list.innerHTML = '<div class="timeline-loading">No activity logged yet.</div>';
        notiList.innerHTML = '<div class="noti-empty">No new activities</div>';
        notiDot.classList.remove('active');
        return;
    }
    
    list.innerHTML = '';
    activities.forEach(act => {
        const date = new Date(act.timestamp);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' - ' + date.toLocaleDateString();
        
        let iconName = 'message-square';
        if (act.type === 'unanswered') iconName = 'help-circle';
        if (act.type === 'resolve') iconName = 'check-circle-2';
        
        const node = document.createElement('div');
        node.className = `activity-node ${act.type}`;
        node.innerHTML = `
            <div class="activity-node-icon">
                <i data-lucide="${iconName}"></i>
            </div>
            <div class="activity-node-body">
                <p>${act.message}</p>
                <span class="activity-node-time">${timeStr}</span>
            </div>
        `;
        list.appendChild(node);
    });
    
    notiList.innerHTML = '';
    activities.slice(0, 5).forEach(act => {
        const date = new Date(act.timestamp);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let iconName = 'message-square';
        if (act.type === 'unanswered') iconName = 'help-circle';
        if (act.type === 'resolve') iconName = 'check-circle-2';
        
        const item = document.createElement('div');
        item.className = `noti-item ${act.type}`;
        item.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <div>
                <p>${act.message}</p>
                <span class="noti-time">${timeStr}</span>
            </div>
        `;
        notiList.appendChild(item);
    });
    
    notiDot.classList.add('active');
    lucide.createIcons();
}

function renderTopQueries(topQueries) {
    const list = document.getElementById('top-queries-list');
    
    if (!topQueries || topQueries.length === 0) {
        list.innerHTML = '<div class="timeline-loading">No popular queries detected yet.</div>';
        return;
    }
    
    list.innerHTML = '';
    topQueries.forEach((q, idx) => {
        const node = document.createElement('div');
        node.className = 'activity-node chat';
        node.innerHTML = `
            <div class="activity-node-icon" style="color: var(--accent-warning); border-color: rgba(245, 158, 11, 0.2);">
                <span>#${idx + 1}</span>
            </div>
            <div class="activity-node-body">
                <p style="font-weight: 500;">"${q.question}"</p>
                <span class="activity-node-time">${q.count} times searched</span>
            </div>
        `;
        list.appendChild(node);
    });
}

// ----------------- Create Persona Simulator -----------------

function handleCreateUserPersona(e) {
    e.preventDefault();
    const name = document.getElementById('create-user-name').value.trim();
    const email = document.getElementById('create-user-email').value.trim();
    const platform = document.getElementById('create-user-platform').value;
    
    // Generate unique random 4-digit ID
    const randomId = Math.floor(1000 + Math.random() * 9000);
    const userId = `USR-${randomId}`;
    
    // Add option to select
    const select = document.getElementById('chat-user-select');
    const option = document.createElement('option');
    option.value = userId;
    option.text = `${name} (${userId})`;
    select.appendChild(option);
    
    // Store metadata so the fetch request maps it
    localStorage.setItem(`persona_metadata_${userId}`, JSON.stringify({ name, email, platform }));
    
    // Select the new user persona
    select.value = userId;
    
    // Clean up and close modal
    document.getElementById('create-user-name').value = '';
    document.getElementById('create-user-email').value = '';
    document.getElementById('user-create-modal').classList.remove('open');
    
    showSuccessNotification(`Created tester profile: ${name}`);
    loadChatHistory(userId);
}

// ----------------- Voice Recognition (Speech to Text) -----------------

function toggleVoiceRecognition() {
    if (!recognition) {
        alert('Web Speech API is not supported in this browser. Try Chrome or Edge.');
        return;
    }
    
    const micBtn = document.getElementById('chat-mic-btn');
    const selectedLang = document.getElementById('chat-lang-select').value;
    
    if (isListening) {
        recognition.stop();
        isListening = false;
        micBtn.classList.remove('listening');
    } else {
        recognition.lang = selectedLang === 'kn' ? 'kn-IN' : 'en-IN';
        recognition.start();
        isListening = true;
        micBtn.classList.add('listening');
        
        recognition.onresult = (event) => {
            const transcriptText = event.results[0][0].transcript;
            const chatInput = document.getElementById('chat-input');
            chatInput.value = transcriptText;
            chatInput.focus();
            micBtn.classList.remove('listening');
            isListening = false;
            triggerSuggestionsFetch(transcriptText);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            micBtn.classList.remove('listening');
            isListening = false;
        };
        
        recognition.onend = () => {
            micBtn.classList.remove('listening');
            isListening = false;
        };
    }
}

// ----------------- Voice Synthesis (Text to Speech) -----------------

function speakBotResponse(text) {
    const voiceResponseToggle = document.getElementById('voice-response-toggle');
    const isEnabled = voiceResponseToggle.getAttribute('data-enabled') === 'true';
    if (!isEnabled || !('speechSynthesis' in window)) return;
    
    window.speechSynthesis.cancel();
    
    const selectedLang = document.getElementById('chat-lang-select').value;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLang === 'kn' ? 'kn-IN' : 'en-IN';
    
    window.speechSynthesis.speak(utterance);
}

// ----------------- Autocomplete Search Suggestions -----------------

async function triggerSuggestionsFetch(text) {
    const suggestionsBox = document.getElementById('search-suggestions');
    if (!text.trim()) {
        suggestionsBox.classList.add('hidden');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/suggestions?q=${encodeURIComponent(text)}`);
        if (res.ok) {
            const list = await res.json();
            if (list.length > 0) {
                suggestionsBox.innerHTML = '';
                list.forEach(item => {
                    const row = document.createElement('div');
                    row.className = 'suggestion-item';
                    row.textContent = item;
                    row.addEventListener('click', () => {
                        const input = document.getElementById('chat-input');
                        input.value = item;
                        suggestionsBox.classList.add('hidden');
                        sendMessage();
                    });
                    suggestionsBox.appendChild(row);
                });
                suggestionsBox.classList.remove('hidden');
            } else {
                suggestionsBox.classList.add('hidden');
            }
        }
    } catch (err) {
        console.error('Error fetching suggestions', err);
    }
}

// ----------------- Ask to Bot Chat sandbox -----------------

async function loadChatHistory(userId) {
    const chatStream = document.getElementById('chat-stream');
    chatStream.innerHTML = '';
    
    try {
        const res = await fetch(`${API_BASE}/api/history?user_id=${userId}`);
        if (res.ok) {
            const history = await res.json();
            if (history.length > 0) {
                history.forEach(msg => {
                    if (msg.sender === 'user') {
                        appendChatBubble('user', msg.message, '', [], null, msg.timestamp);
                    } else {
                        appendChatBubble('bot', msg.message, '', [], msg.chat_id, msg.timestamp, msg.feedback_rating);
                    }
                });
                chatStream.scrollTop = chatStream.scrollHeight;
                return;
            }
        }
    } catch (err) {
        console.error('Error loading history from server, using empty default', err);
    }
    
    // Default bubble
    chatStream.innerHTML = `
        <div class="chat-bubble bot-message glass">
            <div class="bubble-content">
                <p>Hello! I am Dept. CsBot, Department of Computer Science. I keep MCA and MSc(Cs) information separate, including admission dates, eligibility, fees, curriculum, placements, scholarships, hostel facilities, and notices.</p>
                <span class="bubble-meta">System &bull; Now</span>
            </div>
        </div>
    `;
}

async function sendMessage(e) {
    if (e) e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    document.getElementById('search-suggestions').classList.add('hidden');
    
    const select = document.getElementById('chat-user-select');
    const selectedUserId = select.value;
    const selectedName = select.options[select.selectedIndex].text.split(' (')[0];
    
    // Load metadata details if profile was created locally
    let platform = 'Web Widget';
    let email = `${selectedName.replace(' ', '').lower()}@example.com`;
    const storedMeta = localStorage.getItem(`persona_metadata_${selectedUserId}`);
    if (storedMeta) {
        const meta = JSON.parse(storedMeta);
        platform = meta.platform;
        email = meta.email;
    } else {
        if (selectedUserId === 'USR-2041') platform = 'WhatsApp';
        if (selectedUserId === 'USR-3055') platform = 'Telegram';
    }
    
    appendChatBubble('user', message);
    
    const typingBubble = showTypingIndicator();
    
    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: selectedUserId,
                name: selectedName,
                email: email,
                platform: platform,
                message: message
            })
        });
        
        typingBubble.remove();
        
        if (res.ok) {
            const data = await res.json();

            speakBotResponse(data.answer);
            appendChatBubble('bot', data.answer, '', data.suggestions, data.chat_id);
            loadUnansweredBadgeCount();
        } else {
            appendChatBubble('bot', 'Oops, something went wrong communicating with the NLP backend server.');
        }
    } catch (err) {
        typingBubble.remove();
        appendChatBubble('bot', 'Network Connection Error. Make sure your Python Flask backend is running on port 5000.');
    }
}

function appendChatBubble(sender, text, metaHTML = '', suggestions = [], chatId = null, timestampStr = null, initialRating = null) {
    const stream = document.getElementById('chat-stream');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender === 'user' ? 'user-message' : 'bot-message glass'}`;
    
    const timeStr = timestampStr ? new Date(timestampStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let feedbackHTML = '';
    if (sender === 'bot' && chatId) {
        feedbackHTML = `
            <div class="feedback-container star-rating" data-chat-id="${chatId}">
                <span class="star-btn" data-value="1"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="2"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="3"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="4"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="5"><i data-lucide="star"></i></span>
            </div>
        `;
    }
    
    let suggestionsHTML = '';
    if (suggestions && suggestions.length > 0) {
        suggestionsHTML = `<div class="suggestion-chips-container">`;
        suggestions.forEach(s => {
            suggestionsHTML += `<button class="suggestion-chip" data-query="${s}">${s}</button>`;
        });
        suggestionsHTML += `</div>`;
    }
    
    bubble.innerHTML = `
        <div class="bubble-content">
            <p>${text}</p>
            ${suggestionsHTML}
            <div class="bubble-footer-meta">
                <span class="bubble-meta">${metaHTML} ${sender === 'user' ? 'You' : 'Bot'} &bull; ${timeStr}</span>
                ${feedbackHTML}
            </div>
        </div>
    `;
    
    stream.appendChild(bubble);
    stream.scrollTop = stream.scrollHeight;
    
    lucide.createIcons();
    
    if (sender === 'bot' && chatId) {
        bindStarRatingEvents(bubble, chatId, initialRating);
    }
    
    bindSuggestionClickListeners();
}

function bindStarRatingEvents(bubbleElement, chatId, initialRating) {
    const starsContainer = bubbleElement.querySelector('.star-rating');
    if (!starsContainer) return;
    
    const stars = starsContainer.querySelectorAll('.star-btn');
    let currentRating = initialRating || 0;
    
    // Set initial active states
    if (currentRating > 0) {
        highlightStars(stars, currentRating);
        lockRatingUI(starsContainer, currentRating);
    }
    
    stars.forEach(star => {
        star.addEventListener('mouseenter', () => {
            if (starsContainer.classList.contains('locked')) return;
            const val = parseInt(star.getAttribute('data-value'));
            highlightStars(stars, val);
        });
        
        star.addEventListener('mouseleave', () => {
            if (starsContainer.classList.contains('locked')) return;
            highlightStars(stars, currentRating);
        });
        
        star.addEventListener('click', async () => {
            if (starsContainer.classList.contains('locked')) return;
            const val = parseInt(star.getAttribute('data-value'));
            currentRating = val;
            highlightStars(stars, val);
            
            try {
                const res = await fetch(`${API_BASE}/api/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chat_id: chatId, rating: val })
                });
                
                if (res.ok) {
                    lockRatingUI(starsContainer, val);
                    showSuccessNotification(`Submitted feedback rating: ${val} stars!`);
                }
            } catch (err) {
                console.error('Failed to submit star rating feedback', err);
            }
        });
    });
}

function highlightStars(stars, val) {
    stars.forEach(s => {
        const starVal = parseInt(s.getAttribute('data-value'));
        const icon = s.querySelector('i');
        if (starVal <= val) {
            s.classList.add('active');
            if (icon) {
                icon.setAttribute('fill', '#fbbf24');
                icon.style.color = '#fbbf24';
            }
        } else {
            s.classList.remove('active');
            if (icon) {
                icon.removeAttribute('fill');
                icon.style.color = 'var(--text-muted)';
            }
        }
    });
}

function lockRatingUI(container, val) {
    container.classList.add('locked');
    container.title = `Rated ${val} stars`;
    // Add text label
    const label = document.createElement('span');
    label.className = 'feedback-rated-tag text-success';
    label.style.marginLeft = '8px';
    label.style.fontSize = '0.75rem';
    label.innerHTML = `<i data-lucide="check-circle-2" style="width: 12px; height: 12px; display: inline; vertical-align: middle;"></i> ${val}★`;
    container.appendChild(label);
    lucide.createIcons();
}

function bindSuggestionClickListeners() {
    const chips = document.querySelectorAll('.suggestion-chip');
    chips.forEach(chip => {
        if (!chip.onclick) {
            chip.onclick = () => {
                const query = chip.getAttribute('data-query');
                const chatInput = document.getElementById('chat-input');
                chatInput.value = query;
                sendMessage();
            };
        }
    });
}

function showTypingIndicator() {
    const stream = document.getElementById('chat-stream');
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble typing-bubble glass';
    bubble.innerHTML = `
        <div class="typing-loader">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    stream.appendChild(bubble);
    stream.scrollTop = stream.scrollHeight;
    return bubble;
}

// ----------------- Unanswered Queue Portal -----------------

async function loadUnansweredQueue() {
    const list = document.getElementById('unanswered-list');
    
    try {
        const res = await fetch(`${API_BASE}/api/unanswered`);
        if (!res.ok) return;
        
        unansweredQueries = await res.json();
        
        if (unansweredQueries.length === 0) {
            list.innerHTML = `
                <div class="queue-empty-state">
                    <i data-lucide="shield-check"></i>
                    <h3>Zero Pending Enquiries</h3>
                    <p>The chatbot has matching intents for all logged questions.</p>
                </div>
            `;
            disableResolvePanel();
            lucide.createIcons();
            return;
        }
        
        list.innerHTML = '';
        unansweredQueries.forEach(q => {
            const date = new Date(q.timestamp);
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' - ' + date.toLocaleDateString();
            
            const card = document.createElement('div');
            card.className = `unanswered-card glass ${selectedUnansweredId === q.id ? 'active' : ''}`;
            card.setAttribute('data-id', q.id);
            card.innerHTML = `
                <div class="unanswered-card-header">
                    <div class="unanswered-card-user">
                        <img src="https://api.dicebear.com/7.x/initials/svg?seed=${q.user_name}" alt="User">
                        <span>${q.user_name} (${q.user_id})</span>
                    </div>
                    <span class="unanswered-card-time">${timeStr}</span>
                </div>
                <div class="unanswered-card-body">
                    <p>"${q.question}"</p>
                </div>
            `;
            
            card.addEventListener('click', () => selectUnansweredQuery(q));
            list.appendChild(card);
        });
        
    } catch (err) {
        console.error('Error fetching unanswered questions', err);
    }
}

function selectUnansweredQuery(query) {
    selectedUnansweredId = query.id;
    
    document.querySelectorAll('.unanswered-card').forEach(card => {
        if (card.getAttribute('data-id') === String(query.id)) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });

    const resolvePanel = document.getElementById('resolve-panel');
    const emptyState = document.getElementById('resolve-empty-state');
    const content = document.getElementById('resolve-form-content');
    
    resolvePanel.classList.remove('disabled');
    emptyState.classList.add('hidden');
    content.classList.remove('hidden');
    
    document.getElementById('resolve-id').value = query.id;
    document.getElementById('display-query-text').textContent = `"${query.question}"`;
    document.getElementById('resolve-user-display').value = `${query.user_name} (${query.user_id})`;
    document.getElementById('resolve-answer').value = '';
    document.getElementById('resolve-kannada-answer').value = '';
    document.getElementById('resolve-answer').focus();
}

function disableResolvePanel() {
    selectedUnansweredId = null;
    const resolvePanel = document.getElementById('resolve-panel');
    const emptyState = document.getElementById('resolve-empty-state');
    const content = document.getElementById('resolve-form-content');
    
    resolvePanel.classList.add('disabled');
    emptyState.classList.remove('hidden');
    content.classList.add('hidden');
}

async function submitResolveAnswer(e) {
    e.preventDefault();
    
    const id = document.getElementById('resolve-id').value;
    const answer = document.getElementById('resolve-answer').value.trim();
    const category = document.getElementById('resolve-category').value;
    const kannadaAnswer = document.getElementById('resolve-kannada-answer').value.trim();
    
    if (!id || !answer) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/unanswered/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: parseInt(id),
                answer: answer,
                category: category,
                kannada_answer: kannadaAnswer
            })
        });
        
        if (res.ok) {
            showSuccessNotification('Query resolved and injected into AI Knowledge Base!');
            selectedUnansweredId = null;
            disableResolvePanel();
            loadUnansweredQueue();
            loadUnansweredBadgeCount();
        } else {
            alert('Failed to resolve query on backend.');
        }
    } catch (err) {
        alert('Error connecting to the Flask resolve endpoint.');
    }
}

function showSuccessNotification(msg) {
    const toast = document.createElement('div');
    toast.className = 'glass';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.background = 'rgba(16, 185, 129, 0.9)';
    toast.style.border = '1px solid rgba(16, 185, 129, 0.4)';
    toast.style.color = 'white';
    toast.style.padding = '14px 24px';
    toast.style.borderRadius = '12px';
    toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
    toast.style.zIndex = '2000';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.animation = 'bubble-fade-in 0.3s ease-out';
    toast.innerHTML = `<i data-lucide="check-circle-2"></i> <span>${msg}</span>`;
    
    document.body.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// ----------------- Bot Users Registry List -----------------

async function loadBotUsers() {
    try {
        const res = await fetch(`${API_BASE}/api/users`);
        if (!res.ok) return;
        
        botUsers = await res.json();
        renderUsersList();
    } catch (err) {
        console.error('Error fetching bot users list', err);
    }
}

function renderUsersList() {
    const tableBody = document.getElementById('users-table-body');
    const searchVal = document.getElementById('user-search-input').value.toLowerCase();
    const statusVal = document.getElementById('user-status-filter').value;
    
    tableBody.innerHTML = '';
    
    const filteredUsers = botUsers.filter(u => {
        const matchesSearch = u.name.toLowerCase().includes(searchVal) || 
                              u.id.toLowerCase().includes(searchVal);
                              
        const matchesStatus = statusVal === 'all' || u.status === statusVal;
        
        return matchesSearch && matchesStatus;
    });
    
    if (filteredUsers.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="timeline-loading" style="text-align: center; padding: 32px 0;">
                    No user profiles match the selected filters.
                </td>
            </tr>
        `;
        return;
    }
    
    filteredUsers.forEach(u => {
        const date = new Date(u.last_active);
        const activeStr = u.last_active ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' - ' + date.toLocaleDateString() : 'Never';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="user-cell">
                    <img class="user-cell-avatar" src="https://api.dicebear.com/7.x/initials/svg?seed=${u.name}" alt="${u.name}">
                    <div class="user-cell-info">
                        <h4>${u.name}</h4>
                        <span>ID: ${u.id} &bull; ${u.email}</span>
                    </div>
                </div>
            </td>
            <td>${u.queries_count}</td>
            <td>${activeStr}</td>
            <td><span class="badge ${u.status === 'Online' ? 'badge-success' : 'badge-indigo'}">${u.status}</span></td>
            <td class="text-right">
                <button class="btn-icon view-history-btn" data-id="${u.id}" title="View conversation transcripts">
                    <i data-lucide="eye"></i>
                </button>
            </td>
        `;
        
        row.querySelector('.view-history-btn').addEventListener('click', () => openUserProfile(u.id));
        tableBody.appendChild(row);
    });
    
    lucide.createIcons();
}

function openUserProfile(userId) {
    const user = botUsers.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('modal-user-avatar').src = `https://api.dicebear.com/7.x/initials/svg?seed=${user.name}`;
    document.getElementById('modal-user-name').textContent = user.name;
    document.getElementById('modal-user-id').textContent = user.id;
    
    document.getElementById('modal-meta-platform').textContent = user.platform;
    document.getElementById('modal-meta-queries').textContent = user.queries_count;
    document.getElementById('modal-meta-accuracy').textContent = `${user.accuracy_rate}%`;
    
    const date = new Date(user.last_active);
    document.getElementById('modal-meta-active').textContent = user.last_active ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never';
    
    const transcript = document.getElementById('modal-transcript');
    transcript.innerHTML = '';
    
    if (!user.history || user.history.length === 0) {
        transcript.innerHTML = '<div class="timeline-loading">No transcript logs recorded for this session.</div>';
    } else {
        user.history.forEach(msg => {
            const bubble = document.createElement('div');
            bubble.className = `modal-chat-bubble ${msg.sender === 'user' ? 'user' : 'bot'}`;
            
            const date = new Date(msg.timestamp);
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            const ratingText = msg.feedback_rating !== undefined && msg.feedback_rating !== null ? ` &bull; Rated ${msg.feedback_rating}★` : '';
            
            bubble.innerHTML = `
                <p>${msg.message}</p>
                <span class="modal-bubble-meta">${msg.sender === 'user' ? 'User' : 'Bot'}${ratingText} &bull; ${timeStr}</span>
            `;
            transcript.appendChild(bubble);
        });
        
        setTimeout(() => transcript.scrollTop = transcript.scrollHeight, 100);
    }
    
    document.getElementById('user-modal').classList.add('open');
}

// ----------------- Knowledge Base CRUD manager -----------------

async function loadKnowledgeBase() {
    try {
        const res = await fetch(`${API_BASE}/api/kb`);
        if (!res.ok) return;
        kbItems = await res.json();
        renderKBList();
    } catch (err) {
        console.error('Error fetching knowledge base items', err);
    }
}

function renderKBList() {
    const tableBody = document.getElementById('kb-table-body');
    const searchVal = document.getElementById('kb-search-input').value.toLowerCase();
    const categoryVal = document.getElementById('kb-category-filter').value;
    
    tableBody.innerHTML = '';
    
    const filteredKB = kbItems.filter(item => {
        const matchesSearch = item.question.toLowerCase().includes(searchVal) || 
                              item.answer.toLowerCase().includes(searchVal) ||
                              (item.kannada_question && item.kannada_question.toLowerCase().includes(searchVal)) ||
                              (item.kannada_answer && item.kannada_answer.toLowerCase().includes(searchVal));
                              
        const matchesCategory = categoryVal === 'all' || item.category === categoryVal;
        
        return matchesSearch && matchesCategory;
    });
    
    if (filteredKB.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="timeline-loading" style="text-align: center; padding: 32px 0;">
                    No FAQ items found matching filters.
                </td>
            </tr>
        `;
        return;
    }
    
    filteredKB.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="badge badge-indigo">${item.category}</span></td>
            <td>
                <div style="font-weight: 500;">${item.question}</div>
                ${item.kannada_question ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">KN: ${item.kannada_question}</div>` : ''}
            </td>
            <td>
                <div style="font-size: 0.85rem; line-height: 1.4; color: var(--text-muted); max-height: 60px; overflow: hidden; text-overflow: ellipsis;">${item.answer}</div>
                ${item.kannada_answer ? `<div style="font-size:0.72rem; color:rgba(99, 102, 241, 0.6); margin-top:2px; max-height: 40px; overflow: hidden;">KN: ${item.kannada_answer}</div>` : ''}
            </td>
            <td class="text-right">
                <div style="display:flex; justify-content:flex-end; gap:8px;">
                    <button class="btn-icon edit-kb-btn" data-id="${item.id}" title="Edit FAQ Entry" style="color:var(--accent-indigo);">
                        <i data-lucide="edit-3"></i>
                    </button>
                    <button class="btn-icon delete-kb-btn" data-id="${item.id}" title="Delete FAQ Entry" style="color:var(--accent-danger);">
                        <i data-lucide="trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        row.querySelector('.edit-kb-btn').addEventListener('click', () => openEditKBModal(item));
        row.querySelector('.delete-kb-btn').addEventListener('click', () => deleteKBItem(item.id));
        
        tableBody.appendChild(row);
    });
    
    lucide.createIcons();
}

function openAddKBModal() {
    document.getElementById('kb-modal-title').textContent = 'Add Q&A Entry';
    document.getElementById('kb-id').value = '';
    document.getElementById('kb-category').value = 'Admissions';
    document.getElementById('kb-question').value = '';
    document.getElementById('kb-answer').value = '';
    document.getElementById('kb-kannada-question').value = '';
    document.getElementById('kb-kannada-answer').value = '';
    
    document.getElementById('kb-modal').classList.add('open');
    document.getElementById('kb-question').focus();
}

function openEditKBModal(item) {
    document.getElementById('kb-modal-title').textContent = 'Edit FAQ Entry';
    document.getElementById('kb-id').value = item.id;
    document.getElementById('kb-category').value = item.category;
    document.getElementById('kb-question').value = item.question;
    document.getElementById('kb-answer').value = item.answer;
    document.getElementById('kb-kannada-question').value = item.kannada_question || '';
    document.getElementById('kb-kannada-answer').value = item.kannada_answer || '';
    
    document.getElementById('kb-modal').classList.add('open');
    document.getElementById('kb-question').focus();
}

async function submitKBForm(e) {
    e.preventDefault();
    
    const id = document.getElementById('kb-id').value;
    const category = document.getElementById('kb-category').value;
    const question = document.getElementById('kb-question').value.trim();
    const answer = document.getElementById('kb-answer').value.trim();
    const kannadaQuestion = document.getElementById('kb-kannada-question').value.trim();
    const kannadaAnswer = document.getElementById('kb-kannada-answer').value.trim();
    
    const payload = { category, question, answer, kannada_question: kannadaQuestion, kannada_answer: kannadaAnswer };
    
    try {
        let res;
        if (id) {
            res = await fetch(`${API_BASE}/api/kb/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            res = await fetch(`${API_BASE}/api/kb`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        
        if (res.ok) {
            showSuccessNotification(id ? 'FAQ entry updated successfully' : 'FAQ entry created successfully');
            document.getElementById('kb-modal').classList.remove('open');
            loadKnowledgeBase();
        } else {
            alert('Failed to save Knowledge Base FAQ.');
        }
    } catch (err) {
        console.error('Error saving FAQ item', err);
    }
}

async function deleteKBItem(id) {
    if (!confirm('Are you sure you want to permanently delete this FAQ from the Knowledge Base?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/kb/${id}`, {
            method: 'DELETE'
        });
        
        if (res.ok) {
            showSuccessNotification('FAQ entry deleted successfully');
            loadKnowledgeBase();
        } else {
            alert('Failed to delete FAQ entry.');
        }
    } catch (err) {
        console.error('Error deleting FAQ item', err);
    }
}

// ----------------- Chart.js Configurations -----------------

function initCharts() {
    const lineCtx = document.getElementById('messageVolumeChart').getContext('2d');
    const gradIndigo = lineCtx.createLinearGradient(0, 0, 0, 250);
    gradIndigo.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    gradIndigo.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
    
    charts.volume = new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
            datasets: [{
                label: 'Processed Queries',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: '#6366f1',
                borderWidth: 3,
                backgroundColor: gradIndigo,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#8b5cf6',
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
                    border: { dash: [5, 5] }
                }
            }
        }
    });

}

function updateChartsData() {
    if (!charts.volume) return;
    
    // Update daily usage line chart with real database aggregate stats
    if (systemStats.daily_usage && systemStats.daily_usage.length > 0) {
        // extract label days and counts
        const labels = systemStats.daily_usage.map(item => {
            // Format date string to display month/day (e.g. 06/20)
            const parts = item.day.split('-');
            return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : item.day;
        });
        const data = systemStats.daily_usage.map(item => item.count);
        
        charts.volume.data.labels = labels;
        charts.volume.data.datasets[0].data = data;
    } else {
        charts.volume.data.datasets[0].data = [0, 0, 0, 0, 0, 0, 0];
    }
    charts.volume.update();
}

// ----------------- Student Portal Event Listeners & Tab Managers -----------------

function setupUserEventListeners() {
    // User sidebar tabs navigation click handler
    const navItems = document.querySelectorAll('.user-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            switchUserTab(tabId);
            const userSidebar = document.getElementById('user-sidebar');
            if (userSidebar) userSidebar.classList.remove('open');
        });
    });

    // Mobile sidebar toggle for user portal
    const userMobileToggle = document.getElementById('user-mobile-toggle');
    if (userMobileToggle) {
        userMobileToggle.addEventListener('click', () => {
            document.getElementById('user-sidebar').classList.add('open');
        });
    }

    // Tap outside student mobile sidebar to close it
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('user-sidebar');
        const toggle = document.getElementById('user-mobile-toggle');
        if (window.innerWidth <= 768 && 
            sidebar && toggle &&
            !sidebar.contains(e.target) && 
            !toggle.contains(e.target) && 
            sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });

    // Theme Switcher for user portal
    const userThemeToggle = document.getElementById('user-theme-toggle');
    if (userThemeToggle) {
        userThemeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
        });
    }

    // Logout
    const logoutBtn = document.getElementById('user-logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleStudentLogout);
    }

    // Chat submit
    const chatForm = document.getElementById('user-chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', sendUserMessage);
    }

    // Clear Chat
    const clearChatBtn = document.getElementById('user-clear-chat');
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            const stream = document.getElementById('user-chat-stream');
            if (stream) {
                stream.innerHTML = `
                    <div class="chat-bubble bot-message glass">
                        <div class="bubble-content">
                            <p>Chat history cleared. How can I help you today?</p>
                            <span class="bubble-meta">System &bull; Now</span>
                        </div>
                    </div>
                `;
            }
        });
    }

    // Suggested Questions for user
    document.querySelectorAll('.user-faq-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const queryText = btn.getAttribute('data-query');
            const chatInput = document.getElementById('user-chat-input');
            if (chatInput) {
                chatInput.value = queryText;
                chatInput.focus();
                triggerUserSuggestionsFetch(queryText);
            }
        });
    });

    // Chat suggestions typing autocomplete
    const chatInput = document.getElementById('user-chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', (e) => {
            triggerUserSuggestionsFetch(e.target.value);
        });
    }

    // Voice recognition mic
    const micBtn = document.getElementById('user-chat-mic-btn');
    if (micBtn) {
        micBtn.addEventListener('click', toggleUserVoiceRecognition);
    }

    // Text to Speech speaker button
    const speakerToggle = document.getElementById('user-voice-response-toggle');
    if (speakerToggle) {
        speakerToggle.addEventListener('click', () => {
            const isEnabled = speakerToggle.getAttribute('data-enabled') === 'true';
            if (isEnabled) {
                speakerToggle.setAttribute('data-enabled', 'false');
                speakerToggle.title = 'Toggle Voice Response (Muted)';
                speakerToggle.innerHTML = '<i data-lucide="volume-x"></i>';
                if (window.speechSynthesis) window.speechSynthesis.cancel();
            } else {
                speakerToggle.setAttribute('data-enabled', 'true');
                speakerToggle.title = 'Toggle Voice Response (Active)';
                speakerToggle.innerHTML = '<i data-lucide="volume-2"></i>';
            }
            lucide.createIcons();
        });
    }

    // Star selector feedback
    const starContainer = document.getElementById('feedback-star-selector');
    if (starContainer) {
        const stars = starContainer.querySelectorAll('.star-select-btn');
        stars.forEach(star => {
            star.addEventListener('click', () => {
                const rating = parseInt(star.getAttribute('data-value'));
                highlightSelectStars(stars, rating);
                starContainer.setAttribute('data-rating-value', rating);
            });
        });
    }

    // General feedback form submit
    const generalFeedbackForm = document.getElementById('general-feedback-form');
    if (generalFeedbackForm) {
        generalFeedbackForm.addEventListener('submit', handleGeneralFeedbackSubmit);
    }
}

function switchUserTab(tabId) {
    currentUserTab = tabId;
    
    document.querySelectorAll('.user-nav-item').forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    document.querySelectorAll('#user-container .view-section').forEach(view => {
        const id = view.getAttribute('id');
        if (id === `view-${tabId}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    const titleMap = {
        'user-dashboard': 'Student Dashboard',
        'user-ask-bot': 'ASK to Bot Assistance',
        'user-notices': 'College Notice Board',
        'user-feedback': 'Share General Feedback'
    };
    const titleEl = document.getElementById('user-page-title');
    if (titleEl) titleEl.textContent = titleMap[tabId] || 'Student Portal';
    
    if (tabId === 'user-dashboard') {
        loadUserDashboardData();
    } else if (tabId === 'user-ask-bot') {
        loadUserChatHistory();
    } else if (tabId === 'user-notices') {
        loadStudentNotices();
    }
}

function highlightSelectStars(stars, rating) {
    stars.forEach(star => {
        const val = parseInt(star.getAttribute('data-value'));
        const icon = star.querySelector('i');
        if (val <= rating) {
            star.classList.add('active');
            if (icon) {
                icon.setAttribute('fill', '#fbbf24');
                icon.style.color = '#fbbf24';
            }
        } else {
            star.classList.remove('active');
            if (icon) {
                icon.removeAttribute('fill');
                icon.style.color = 'var(--text-muted)';
            }
        }
    });
}

async function handleGeneralFeedbackSubmit(e) {
    e.preventDefault();
    const starContainer = document.getElementById('feedback-star-selector');
    const rating = starContainer ? starContainer.getAttribute('data-rating-value') : null;
    const comments = document.getElementById('feedback-comments').value.trim();
    
    if (!rating) {
        alert("Please select a star rating!");
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/general-feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                rating: parseInt(rating),
                comments: comments
            })
        });
        
        if (res.ok) {
            showSuccessNotification("Feedback submitted successfully! Thank you.");
            document.getElementById('general-feedback-form').reset();
            const stars = starContainer.querySelectorAll('.star-select-btn');
            highlightSelectStars(stars, 0);
            starContainer.removeAttribute('data-rating-value');
            
            // Return to Student Dashboard
            switchUserTab('user-dashboard');
        } else {
            alert("Failed to submit feedback.");
        }
    } catch (e) {
        console.error(e);
        alert("Server connection error during feedback submission.");
    }
}

// ----------------- Student Dashboard notices and statistics loader -----------------

async function loadUserDashboardData() {
    if (!currentUser) return;
    
    const welcomeTitle = document.getElementById('user-welcome-title');
    if (welcomeTitle) welcomeTitle.textContent = `Welcome back, ${currentUser.name}!`;
    
    // Sync statistics
    try {
        const res = await fetch(`${API_BASE}/api/users`);
        if (res.ok) {
            const users = await res.json();
            const syncedUser = users.find(u => u.id === currentUser.user_id);
            if (syncedUser) {
                currentUser.queries_count = syncedUser.queries_count;
                currentUser.accuracy_rate = syncedUser.accuracy_rate;
                localStorage.setItem('userToken', JSON.stringify(currentUser));
            }
        }
    } catch (e) {
        console.error("Failed to sync user dashboard stats from server", e);
    }
    
    const queriesVal = document.getElementById('user-stat-queries');
    if (queriesVal) queriesVal.textContent = currentUser.queries_count || 0;
    
    const accuracyVal = document.getElementById('user-stat-accuracy');
    if (accuracyVal) accuracyVal.textContent = `${currentUser.accuracy_rate || 100}%`;
    
    loadStudentDashboardNotices();
}

async function loadStudentDashboardNotices() {
    const list = document.getElementById('user-dashboard-notices');
    if (!list) return;
    
    list.innerHTML = '';
    
    try {
        const res = await fetch(`${API_BASE}/api/notices`);
        if (res.ok) {
            const notices = await res.json();
            const topNotices = notices.slice(0, 3);
            
            if (topNotices.length === 0) {
                list.innerHTML = '<div class="timeline-loading">No active notices posted yet.</div>';
                return;
            }
            
            topNotices.forEach(n => {
                const date = new Date(n.timestamp);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                const node = document.createElement('div');
                node.className = 'activity-node chat';
                node.innerHTML = `
                    <div class="activity-node-icon" style="color: var(--accent-indigo);">
                        <i data-lucide="bell"></i>
                    </div>
                    <div class="activity-node-body">
                        <h4 style="font-weight: 600; font-size: 0.9rem; color: var(--text-main);">${n.title}</h4>
                        <p style="font-size: 0.8rem; margin-top: 4px; color: var(--text-muted); line-height: 1.4;">${n.content}</p>
                        <span class="activity-node-time">${dateStr}</span>
                    </div>
                `;
                list.appendChild(node);
            });
            lucide.createIcons();
        } else {
            list.innerHTML = '<div class="timeline-loading">Error retrieving notices.</div>';
        }
    } catch (e) {
        console.error(e);
        list.innerHTML = '<div class="timeline-loading">Server connection error.</div>';
    }
}

// ----------------- Notice Board Loader -----------------

async function loadStudentNotices() {
    const container = document.getElementById('user-notices-board');
    if (!container) return;
    
    container.innerHTML = '<div class="timeline-loading">Loading college notice board...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/api/notices`);
        if (res.ok) {
            const notices = await res.json();
            if (notices.length === 0) {
                container.innerHTML = `
                    <div class="queue-empty-state" style="grid-column: 1 / -1; padding: 40px 0; text-align:center; color: var(--text-muted);">
                        <i data-lucide="bell-off" style="width:48px; height:48px; margin-bottom:12px; opacity:0.5;"></i>
                        <h3>Notice Board is Empty</h3>
                        <p>There are no announcements currently published on the notice board.</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }
            
            container.innerHTML = '';
            notices.forEach(n => {
                const date = new Date(n.timestamp);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                const card = document.createElement('div');
                card.className = 'notice-card glass';
                card.innerHTML = `
                    <div class="notice-title" style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">${n.title}</div>
                    <div class="notice-meta" style="margin-top: 6px; font-size: 0.75rem; color: var(--text-muted); display:flex; align-items:center; gap:6px;">
                        <i data-lucide="calendar" style="width: 14px; height: 14px;"></i>
                        <span>Posted on: ${dateStr}</span>
                    </div>
                    <div class="notice-body" style="margin-top: 12px; font-size: 0.85rem; line-height: 1.5; color: var(--text-muted);">${n.content}</div>
                `;
                container.appendChild(card);
            });
            lucide.createIcons();
        } else {
            container.innerHTML = '<div class="timeline-loading">Error loading notice board.</div>';
        }
    } catch (e) {
        console.error(e);
        container.innerHTML = '<div class="timeline-loading">Server connection error.</div>';
    }
}

// ----------------- Chatbot Student Interface -----------------

async function loadUserChatHistory() {
    if (!currentUser) return;
    
    const chatStream = document.getElementById('user-chat-stream');
    if (!chatStream) return;
    
    chatStream.innerHTML = '';
    
    try {
        const res = await fetch(`${API_BASE}/api/history?user_id=${currentUser.user_id}`);
        if (res.ok) {
            const history = await res.json();
            if (history.length > 0) {
                history.forEach(msg => {
                    if (msg.sender === 'user') {
                        appendUserChatBubble('user', msg.message, '', [], null, msg.timestamp);
                    } else {
                        appendUserChatBubble('bot', msg.message, '', [], msg.chat_id, msg.timestamp, msg.feedback_rating);
                    }
                });
                chatStream.scrollTop = chatStream.scrollHeight;
                return;
            }
        }
    } catch (err) {
        console.error('Error loading history from server', err);
    }
    
    // Default welcome message bubble
    chatStream.innerHTML = `
        <div class="chat-bubble bot-message glass">
            <div class="bubble-content">
                <p>Hello! I am Dept. CsBot, Department of Computer Science. I keep MCA and MSc(Cs) information separate, including admission dates, eligibility, fees, curriculum, placements, scholarships, hostel facilities, and notices.</p>
                <span class="bubble-meta">System &bull; Now</span>
            </div>
        </div>
    `;
}

async function sendUserMessage(e) {
    if (e) e.preventDefault();
    
    const input = document.getElementById('user-chat-input');
    if (!input) return;
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    const suggBox = document.getElementById('user-search-suggestions');
    if (suggBox) suggBox.classList.add('hidden');
    
    appendUserChatBubble('user', message);
    const typingBubble = showUserTypingIndicator();
    
    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                name: currentUser.name,
                email: currentUser.email,
                platform: 'Web Portal',
                message: message
            })
        });
        
        typingBubble.remove();
        
        if (res.ok) {
            const data = await res.json();

            speakUserBotResponse(data.answer);
            appendUserChatBubble('bot', data.answer, '', data.suggestions, data.chat_id);
        } else {
            appendUserChatBubble('bot', 'Oops, something went wrong communicating with the NLP backend server.');
        }
    } catch (err) {
        if (typingBubble) typingBubble.remove();
        appendUserChatBubble('bot', 'Network Connection Error. Make sure your Python Flask backend is running.');
    }
}

function appendUserChatBubble(sender, text, metaHTML = '', suggestions = [], chatId = null, timestampStr = null, initialRating = null) {
    const stream = document.getElementById('user-chat-stream');
    if (!stream) return;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender === 'user' ? 'user-message' : 'bot-message glass'}`;
    
    const timeStr = timestampStr ? new Date(timestampStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let feedbackHTML = '';
    if (sender === 'bot' && chatId) {
        feedbackHTML = `
            <div class="feedback-container star-rating" data-chat-id="${chatId}">
                <span class="star-btn" data-value="1"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="2"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="3"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="4"><i data-lucide="star"></i></span>
                <span class="star-btn" data-value="5"><i data-lucide="star"></i></span>
            </div>
        `;
    }
    
    let suggestionsHTML = '';
    if (suggestions && suggestions.length > 0) {
        suggestionsHTML = `<div class="suggestion-chips-container">`;
        suggestions.forEach(s => {
            suggestionsHTML += `<button class="suggestion-chip user-suggestion-chip" data-query="${s}">${s}</button>`;
        });
        suggestionsHTML += `</div>`;
    }
    
    bubble.innerHTML = `
        <div class="bubble-content">
            <p>${text}</p>
            ${suggestionsHTML}
            <div class="bubble-footer-meta">
                <span class="bubble-meta">${metaHTML} ${sender === 'user' ? 'You' : 'Bot'} &bull; ${timeStr}</span>
                ${feedbackHTML}
            </div>
        </div>
    `;
    
    stream.appendChild(bubble);
    stream.scrollTop = stream.scrollHeight;
    
    lucide.createIcons();
    
    if (sender === 'bot' && chatId) {
        bindUserStarRatingEvents(bubble, chatId, initialRating);
    }
    
    bindUserSuggestionClickListeners();
}

function bindUserStarRatingEvents(bubbleElement, chatId, initialRating) {
    const starsContainer = bubbleElement.querySelector('.star-rating');
    if (!starsContainer) return;
    
    const stars = starsContainer.querySelectorAll('.star-btn');
    let currentRating = initialRating || 0;
    
    if (currentRating > 0) {
        highlightStars(stars, currentRating);
        lockRatingUI(starsContainer, currentRating);
    }
    
    stars.forEach(star => {
        star.addEventListener('mouseenter', () => {
            if (starsContainer.classList.contains('locked')) return;
            const val = parseInt(star.getAttribute('data-value'));
            highlightStars(stars, val);
        });
        
        star.addEventListener('mouseleave', () => {
            if (starsContainer.classList.contains('locked')) return;
            highlightStars(stars, currentRating);
        });
        
        star.addEventListener('click', async () => {
            if (starsContainer.classList.contains('locked')) return;
            const val = parseInt(star.getAttribute('data-value'));
            currentRating = val;
            highlightStars(stars, val);
            
            try {
                const res = await fetch(`${API_BASE}/api/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chat_id: chatId, rating: val })
                });
                
                if (res.ok) {
                    lockRatingUI(starsContainer, val);
                    showSuccessNotification(`Submitted response rating: ${val} stars!`);
                }
            } catch (err) {
                console.error('Failed to submit star rating feedback', err);
            }
        });
    });
}

function bindUserSuggestionClickListeners() {
    const chips = document.querySelectorAll('.user-suggestion-chip');
    chips.forEach(chip => {
        if (!chip.onclick) {
            chip.onclick = () => {
                const query = chip.getAttribute('data-query');
                const chatInput = document.getElementById('user-chat-input');
                if (chatInput) {
                    chatInput.value = query;
                    sendUserMessage();
                }
            };
        }
    });
}

function showUserTypingIndicator() {
    const stream = document.getElementById('user-chat-stream');
    if (!stream) return null;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble typing-bubble glass';
    bubble.innerHTML = `
        <div class="typing-loader">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    stream.appendChild(bubble);
    stream.scrollTop = stream.scrollHeight;
    return bubble;
}

async function triggerUserSuggestionsFetch(text) {
    const suggestionsBox = document.getElementById('user-search-suggestions');
    if (!suggestionsBox) return;
    
    if (!text.trim()) {
        suggestionsBox.classList.add('hidden');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/suggestions?q=${encodeURIComponent(text)}`);
        if (res.ok) {
            const list = await res.json();
            if (list.length > 0) {
                suggestionsBox.innerHTML = '';
                list.forEach(item => {
                    const row = document.createElement('div');
                    row.className = 'suggestion-item';
                    row.textContent = item;
                    row.addEventListener('click', () => {
                        const input = document.getElementById('user-chat-input');
                        if (input) {
                            input.value = item;
                            suggestionsBox.classList.add('hidden');
                            sendUserMessage();
                        }
                    });
                    suggestionsBox.appendChild(row);
                });
                suggestionsBox.classList.remove('hidden');
            } else {
                suggestionsBox.classList.add('hidden');
            }
        }
    } catch (err) {
        console.error('Error fetching suggestions', err);
    }
}

// ----------------- User Voice Support (STT and TTS) -----------------

let userRecognition = null;
let isUserListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    userRecognition = new SpeechRecognition();
    userRecognition.continuous = false;
    userRecognition.interimResults = false;
}

function toggleUserVoiceRecognition() {
    if (!userRecognition) {
        alert('Web Speech API is not supported in this browser. Try Chrome or Edge.');
        return;
    }
    
    const micBtn = document.getElementById('user-chat-mic-btn');
    const selectedLang = document.getElementById('user-chat-lang-select').value;
    
    if (isUserListening) {
        userRecognition.stop();
        isUserListening = false;
        if (micBtn) micBtn.classList.remove('listening');
    } else {
        userRecognition.lang = selectedLang === 'kn' ? 'kn-IN' : 'en-IN';
        userRecognition.start();
        isUserListening = true;
        if (micBtn) micBtn.classList.add('listening');
        
        userRecognition.onresult = (event) => {
            const transcriptText = event.results[0][0].transcript;
            const chatInput = document.getElementById('user-chat-input');
            if (chatInput) {
                chatInput.value = transcriptText;
                chatInput.focus();
                triggerUserSuggestionsFetch(transcriptText);
            }
            if (micBtn) micBtn.classList.remove('listening');
            isUserListening = false;
        };
        
        userRecognition.onerror = () => {
            if (micBtn) micBtn.classList.remove('listening');
            isUserListening = false;
        };
        
        userRecognition.onend = () => {
            if (micBtn) micBtn.classList.remove('listening');
            isUserListening = false;
        };
    }
}

function speakUserBotResponse(text) {
    const speakerToggle = document.getElementById('user-voice-response-toggle');
    if (!speakerToggle) return;
    const isEnabled = speakerToggle.getAttribute('data-enabled') === 'true';
    if (!isEnabled || !('speechSynthesis' in window)) return;
    
    window.speechSynthesis.cancel();
    
    const selectedLang = document.getElementById('user-chat-lang-select').value;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLang === 'kn' ? 'kn-IN' : 'en-IN';
    
    window.speechSynthesis.speak(utterance);
}

// ----------------- Notice board and general feedback ADMIN loaders -----------------

async function loadAdminNotices() {
    const tableBody = document.getElementById('admin-notices-table-body');
    if (!tableBody) return;
    
    const searchInput = document.getElementById('admin-notices-search');
    const searchVal = searchInput ? searchInput.value.toLowerCase() : '';
    
    tableBody.innerHTML = '<tr><td colspan="4" class="timeline-loading" style="text-align: center;">Loading notice announcements...</td></tr>';
    
    try {
        const res = await fetch(`${API_BASE}/api/notices`);
        if (res.ok) {
            const notices = await res.json();
            const filteredNotices = notices.filter(n => 
                n.title.toLowerCase().includes(searchVal) || 
                n.content.toLowerCase().includes(searchVal)
            );
            
            if (filteredNotices.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="timeline-loading" style="text-align: center;">No announcements match search criteria.</td></tr>';
                return;
            }
            
            tableBody.innerHTML = '';
            filteredNotices.forEach(n => {
                const date = new Date(n.timestamp);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-weight: 600; color: var(--text-main);">${n.title}</td>
                    <td><div style="font-size: 0.85rem; line-height: 1.4; color: var(--text-muted); max-height: 60px; overflow: hidden; text-overflow: ellipsis;">${n.content}</div></td>
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${dateStr}</td>
                    <td class="text-right">
                        <button class="btn-icon delete-notice-btn" data-id="${n.notice_id}" title="Remove Notice" style="color: var(--accent-danger);">
                            <i data-lucide="trash"></i>
                        </button>
                    </td>
                `;
                
                row.querySelector('.delete-notice-btn').addEventListener('click', () => deleteNoticeItem(n.notice_id));
                tableBody.appendChild(row);
            });
            lucide.createIcons();
        } else {
            tableBody.innerHTML = '<tr><td colspan="4" class="timeline-loading" style="text-align: center; color: var(--accent-danger);">Error fetching notice database.</td></tr>';
        }
    } catch (e) {
        console.error(e);
        tableBody.innerHTML = '<tr><td colspan="4" class="timeline-loading" style="text-align: center; color: var(--accent-danger);">Server connection error.</td></tr>';
    }
}

async function deleteNoticeItem(notice_id) {
    if (!confirm("Are you sure you want to permanently delete this announcement notice?")) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/notices/${notice_id}`, { method: 'DELETE' });
        if (res.ok) {
            showSuccessNotification("Announcement deleted successfully.");
            loadAdminNotices();
        } else {
            alert("Failed to delete notice.");
        }
    } catch (e) {
        console.error(e);
        alert("Server connection error during notice deletion.");
    }
}

async function loadAdminFeedback() {
    const tableBody = document.getElementById('admin-feedback-table-body');
    if (!tableBody) return;
    
    const searchInput = document.getElementById('admin-feedback-search');
    const searchVal = searchInput ? searchInput.value.toLowerCase() : '';
    
    tableBody.innerHTML = '<tr><td colspan="5" class="timeline-loading" style="text-align: center;">Loading student feedback comments...</td></tr>';
    
    try {
        const res = await fetch(`${API_BASE}/api/general-feedback`);
        if (res.ok) {
            const feedbacks = await res.json();
            const filteredFeedbacks = feedbacks.filter(f => 
                f.name.toLowerCase().includes(searchVal) || 
                f.comments.toLowerCase().includes(searchVal) ||
                f.user_id.toLowerCase().includes(searchVal)
            );
            
            if (filteredFeedbacks.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="timeline-loading" style="text-align: center;">No student feedback comments found.</td></tr>';
                return;
            }
            
            tableBody.innerHTML = '';
            filteredFeedbacks.forEach(f => {
                const date = new Date(f.timestamp);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                let starsHTML = '';
                for (let i = 1; i <= 5; i++) {
                    starsHTML += `<i data-lucide="star" style="width: 14px; height: 14px; display: inline-block; color: ${i <= f.rating ? '#fbbf24' : 'var(--text-muted)'};" ${i <= f.rating ? 'fill="#fbbf24"' : ''}></i>`;
                }
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-size: 0.8rem; font-weight: 500;">${f.user_id}</td>
                    <td style="font-weight: 500; color: var(--text-main);">${f.name}</td>
                    <td><div style="display: flex; gap: 2px;">${starsHTML}</div></td>
                    <td><div style="font-size: 0.85rem; line-height: 1.4; color: var(--text-muted); max-height: 60px; overflow: hidden; text-overflow: ellipsis;">"${f.comments}"</div></td>
                    <td class="text-right">
                        <button class="btn-icon delete-feedback-btn" data-id="${f.feedback_id}" title="Remove Feedback" style="color: var(--accent-danger);">
                            <i data-lucide="trash"></i>
                        </button>
                    </td>
                `;
                
                row.querySelector('.delete-feedback-btn').addEventListener('click', () => deleteFeedbackItem(f.feedback_id));
                tableBody.appendChild(row);
            });
            lucide.createIcons();
        } else {
            tableBody.innerHTML = '<tr><td colspan="5" class="timeline-loading" style="text-align: center; color: var(--accent-danger);">Error fetching feedback comments.</td></tr>';
        }
    } catch (e) {
        console.error(e);
        tableBody.innerHTML = '<tr><td colspan="5" class="timeline-loading" style="text-align: center; color: var(--accent-danger);">Server connection error.</td></tr>';
    }
}

async function deleteFeedbackItem(feedback_id) {
    if (!confirm("Are you sure you want to permanently delete this student feedback submission?")) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/general-feedback/${feedback_id}`, { method: 'DELETE' });
        if (res.ok) {
            showSuccessNotification("Feedback deleted successfully.");
            loadAdminFeedback();
        } else {
            alert("Failed to delete feedback.");
        }
    } catch (e) {
        console.error(e);
        alert("Server connection error during feedback deletion.");
    }
}
