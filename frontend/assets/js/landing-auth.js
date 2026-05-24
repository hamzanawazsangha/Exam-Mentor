/**
 * ExamMentor Landing Site Auth Handler
 * Handles dynamic navbar state based on login status
 */

document.addEventListener('DOMContentLoaded', () => {
    updateLandingNavbar();
});

function updateLandingNavbar() {
    const navActions = document.querySelector('.nav-actions');
    if (!navActions) return;

    const user = JSON.parse(localStorage.getItem('user'));
    
    if (user) {
        // Logged In State
        const photo = user.photo_url || '/assets/images/default-avatar.png';
        const firstName = user.first_name || 'Aspirant';

        navActions.innerHTML = `
            <div class="user-menu-container">
                <div class="user-trigger">
                    <img src="${photo}" alt="Profile" class="user-nav-photo" onerror="this.src='/assets/images/default-avatar.png'">
                    <span style="font-weight: 600; color: var(--text-main);">${firstName}</span>
                    <i data-lucide="chevron-down" style="width: 16px; height: 16px;"></i>
                </div>
                <div class="user-dropdown">
                    <a href="/dashboard" class="dropdown-item">
                        <i data-lucide="layout-dashboard" style="width: 18px;"></i>
                        <span>Go to Dashboard</span>
                    </a>
                    <a href="/profile" class="dropdown-item">
                        <i data-lucide="user" style="width: 18px;"></i>
                        <span>My Profile</span>
                    </a>
                    <div style="height: 1px; background: var(--border-color); margin: 8px 0;"></div>
                    <a href="#" onclick="landingLogout(event)" class="dropdown-item logout-item">
                        <i data-lucide="log-out" style="width: 18px;"></i>
                        <span>Logout Session</span>
                    </a>
                </div>
            </div>
        `;
    } else {
        // Logged Out State
        navActions.innerHTML = `
            <div class="user-menu-container">
                <div class="user-trigger">
                    <i data-lucide="user-circle" style="width: 24px; height: 24px; color: var(--primary);"></i>
                    <span style="font-weight: 600; color: var(--text-main);">Account</span>
                </div>
                <div class="user-dropdown">
                    <a href="/login?mode=register" class="dropdown-item">
                        <span>Join Now</span>
                    </a>
                    <a href="/login" class="dropdown-item">
                        <span>Login</span>
                    </a>
                </div>
            </div>
        `;
    }

    if (window.lucide) {
        lucide.createIcons();
    }
}

function landingLogout(e) {
    e.preventDefault();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.reload();
}
