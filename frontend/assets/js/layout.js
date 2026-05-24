// ─────────────────────────────────────────────
// Common Layout & Shared Logic
// ─────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initSharedLayout();
});

function initSharedLayout() {
    // Check authentication for protected pages
    const path = window.location.pathname;
    const isLoginPage = path.includes('login') || path === '/' || path === '';
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    if (!isLoginPage && (!token || !user)) {
        window.location.href = 'login';
        return;
    }

    if (isLoginPage && token && user) {
        window.location.href = 'dashboard';
        return;
    }

    // Inject Sidebar if we are on a portal page
    if (!isLoginPage) {
        injectSidebar();
        injectChatbot();
        injectToastContainer();
        updateUserDisplay();
    } else {
        injectToastContainer();
    }

    // Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }
}

function injectSidebar() {
    const mainApp = document.getElementById('main-app');
    if (!mainApp) return;

    // Check if sidebar already exists
    if (document.querySelector('.sidebar')) return;

    const sidebar = document.createElement('aside');
    sidebar.className = 'sidebar';
    sidebar.innerHTML = `
        <div class="sidebar-header">
            <a href="/" class="logo" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 12px;">
                <img src="/assets/img/logo12.jpg?v=2" alt="ExamMentor Logo" class="custom-logo-img">
                <div>
                    <h1 style="margin: 0; font-size: 1.25rem;">ExamMentor</h1>
                    <span style="font-size: 0.75rem; opacity: 0.8;">PPSC & CSS Portal</span>
                </div>
            </a>
        </div>

        <nav class="sidebar-nav" id="sidebar-links">
            <!-- Dynamic Links Injected Here -->
        </nav>

        <div class="sidebar-footer">
            <button onclick="logout()" class="logout-btn w-100">
                <i data-lucide="log-out"></i>
                <span>Logout Session</span>
            </button>
        </div>
    `;

    mainApp.insertBefore(sidebar, mainApp.firstChild);
    
    // Handle sidebar links
    const sidebarLinks = document.getElementById('sidebar-links');
    if (sidebarLinks) {
        const path = window.location.pathname;
        const activeExam = localStorage.getItem('activeExam');
        const user = JSON.parse(localStorage.getItem('user')) || {};
        const userName = user.first_name ? `${user.first_name} ${user.last_name || ''}` : 'Profile';
        const userPhoto = user.photo_url || `https://ui-avatars.com/api/?name=${user.first_name || 'User'}&background=random`;

        const menuItems = [
            { id: 'nav-dashboard', label: 'Dashboard', icon: 'layout-dashboard', page: 'dashboard' },
            { id: 'nav-preparation', label: 'Preparation', icon: 'graduation-cap', page: 'preparation' },
            { id: 'nav-tracker', label: 'Syllabus Tracker', icon: 'clipboard-check', page: 'syllabus-tracker' },
            { id: 'nav-mock', label: 'Mock Tests', icon: 'book-open', page: 'mock-tests' },
            { id: 'nav-evaluator', label: 'Answer Evaluator', icon: 'check-circle', page: 'answer-evaluator' },
            { id: 'nav-essay', label: 'Essay Studio', icon: 'pen-tool', page: 'essay-studio' },
            { id: 'nav-pastpapers', label: 'Past Papers', icon: 'file-text', page: 'past-papers-repo' },
            { id: 'nav-profile', label: userName, photo: userPhoto, page: 'profile' }
        ];

        // Add Exam Hall dynamically if active test exists
        if (activeExam) {
            menuItems.splice(4, 0, { id: 'nav-exam-hall', label: 'Exam Hall', icon: 'clock', page: 'exam-hall', pulse: true });
        }

        sidebarLinks.innerHTML = menuItems.filter(item => !item.hide).map(item => `
            <a href="${item.page}" class="sidebar-link ${path.includes(item.page) ? 'active' : ''}" id="${item.id}">
                ${item.photo ? `<img src="${item.photo}" class="nav-photo" alt="Me">` : `<i data-lucide="${item.icon}"></i>`}
                <span>${item.label}</span>
                ${item.pulse ? '<span class="pulse-dot"></span>' : ''}
            </a>
        `).join('');

        // Add Navigation Guard for Exam Hall
        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', function(e) {
                if (window.location.pathname.includes('exam-hall')) {
                    const targetPage = this.getAttribute('href');
                    if (targetPage !== 'exam-hall') {
                        e.preventDefault();
                        if (confirm("Warning: Leaving the Exam Hall will automatically submit your paper as-is. Do you want to proceed?")) {
                            if (typeof submitMockTest === 'function') {
                                submitMockTest().then(() => {
                                    window.location.href = targetPage;
                                });
                            } else {
                                window.location.href = targetPage;
                            }
                        }
                    }
                }
            });
        });
    }
    if (window.lucide) {
        lucide.createIcons();
    }
}

function injectChatbot() {
    if (document.getElementById('chat-container')) return;

    const chatHtml = `
        <button id="chat-toggle" class="chat-toggle hidden" onclick="toggleChat()">
            <i data-lucide="message-circle"></i>
        </button>

        <div id="chat-container" class="chat-container hidden">
            <div class="chat-header">
                <div class="d-flex align-items-center gap-2">
                    <img src="/assets/img/logo12.jpg?v=2" alt="Logo" class="custom-logo-img" style="width:24px; height:24px; padding:1px;">
                    <div>
                        <h4 class="m-0">Expert CSS Mentor</h4>
                        <span class="status-online">Mistral Active</span>
                    </div>
                </div>
                <button onclick="toggleChat()" class="close-chat"><i data-lucide="x"></i></button>
            </div>
            <div id="chat-messages" class="chat-messages">
                <div class="message system">
                    Hello! I am your <b>Expert CSS Mentor</b>. Ask me anything about reasoning, exam strategy, or specific subject queries.
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Ask your expert query..." onkeypress="if(event.key==='Enter') sendMentorMessage()">
                <button onclick="sendMentorMessage()"><i data-lucide="send"></i></button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', chatHtml);
}

function injectToastContainer() {
    if (document.getElementById('toast-container')) return;
    const toastHtml = `<div id="toast-container" class="toast-container"></div>`;
    document.body.insertAdjacentHTML('beforeend', toastHtml);
}

function navigateTo(url) {
    window.location.href = url;
}

function updateUserDisplay() {
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        const nameEl = document.getElementById('sidebar-user-name');
        if (nameEl) nameEl.textContent = user.first_name || user.email;
        
        const photoUrl = user.photo_url || `https://ui-avatars.com/api/?name=${user.first_name}+${user.last_name}&background=random`;
        const sidebarPhoto = document.getElementById('sidebar-user-photo');
        if (sidebarPhoto) sidebarPhoto.src = photoUrl;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login';
}
