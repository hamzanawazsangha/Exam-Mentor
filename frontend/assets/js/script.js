// ─────────────────────────────────────────────
// PPSC & CSS AI Portal — Frontend Script
// ─────────────────────────────────────────────

const API = 'http://127.0.0.1:5000/api';
let currentUser = null;
let activeTest = null;
let testTimer = null;

// ── Notification System ─────────────────────
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'check-circle',
        error: 'alert-circle',
        info: 'info'
    };
    
    toast.innerHTML = `
        <div class="toast-icon"><i data-lucide="${iconMap[type] || 'info'}"></i></div>
        <div class="toast-content">
            <span class="toast-title">${title}</span>
            <span class="toast-msg">${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    lucide.createIcons();
    
    // Animate in
    setTimeout(() => toast.classList.add('active'), 10);
    
    // Remove after 5s
    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

function showConfirm(title, message, btnText = 'Delete') {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirm-modal');
        const titleEl = document.getElementById('confirm-title');
        const msgEl = document.getElementById('confirm-msg');
        const btnYes = document.getElementById('confirm-btn-yes');
        
        titleEl.textContent = title;
        msgEl.textContent = message;
        btnYes.textContent = btnText;
        modal.classList.remove('hidden');
        lucide.createIcons();
        
        window.closeConfirm = (res) => {
            modal.classList.add('hidden');
            resolve(res);
        };
        
        btnYes.onclick = () => closeConfirm(true);
    });
}

// ── App Initialization ──────────────────────
function initApp() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    const path = window.location.pathname;
    const isLoginPage = path.includes('login') || path === '/' || path === '';
    
    if (token && user) {
        currentUser = JSON.parse(user);
        
        // If we are on login page but have token, go to dashboard
        if (isLoginPage) {
            window.location.href = 'dashboard';
            return;
        }
        
        // Show chatbot toggle when user is logged in
        const chatToggle = document.getElementById('chat-toggle');
        if (chatToggle) chatToggle.classList.remove('hidden');
        
        // Update greeting if it exists
        const greetingEl = document.getElementById('dash-greeting');
        if (greetingEl) {
            greetingEl.innerHTML = `Welcome Back, ${currentUser.first_name || 'Aspirant'} <i data-lucide="hand" class="icon-inline"></i>`;
        }
        
        // Load page specific data
        if (path.includes('syllabus-tracker')) loadTracker();
        if (path.includes('preparation')) loadPrepOptions();
        if (path.includes('mock-tests')) loadMockSubjects();
        if (path.includes('past-papers-repo')) loadPastPapers();
        if (path.includes('dashboard')) loadDashboardDetails();
        if (path.includes('profile')) loadProfileData();
        
        lucide.createIcons();
    }
}

// ── Auth ─────────────────────────────────────
function switchAuth(section) {
    document.querySelectorAll('.auth-section').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.auth-section').forEach(el => el.classList.remove('active'));
    document.getElementById(`auth-${section}`).classList.remove('hidden');
    document.getElementById(`auth-${section}`).classList.add('active');
    
    // Crucial: Re-render icons on every switch
    lucide.createIcons();
}

// ── Password Validation ──
function validatePassword() {
    const password = document.getElementById('reg-password').value;
    const reqCapital = document.getElementById('req-capital');
    const reqSmall = document.getElementById('req-small');
    const reqNumber = document.getElementById('req-number');
    const reqLength = document.getElementById('req-length');
    
    const hasCapital = /[A-Z]/.test(password);
    const hasSmall = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasLength = password.length >= 8;
    
    // Update capital letter requirement
    if (hasCapital) {
        reqCapital.classList.add('met');
    } else {
        reqCapital.classList.remove('met');
    }
    
    // Update lowercase letter requirement
    if (hasSmall) {
        reqSmall.classList.add('met');
    } else {
        reqSmall.classList.remove('met');
    }
    
    // Update number requirement
    if (hasNumber) {
        reqNumber.classList.add('met');
    } else {
        reqNumber.classList.remove('met');
    }
    
    // Update length requirement
    if (hasLength) {
        reqLength.classList.add('met');
    } else {
        reqLength.classList.remove('met');
    }
}

async function register() {
    const first_name = document.getElementById('reg-first-name').value;
    const last_name = document.getElementById('reg-last-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const btn = document.querySelector('#auth-register .btn-submit');
    const msg = document.getElementById('reg-msg');
    
    // Validate all password requirements
    const hasCapital = /[A-Z]/.test(password);
    const hasSmall = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasLength = password.length >= 8;
    
    if (!hasCapital || !hasSmall || !hasNumber || !hasLength) {
        showToast("Registration Error", "Password must meet all requirements: uppercase, lowercase, number, and at least 8 characters.", "error");
        return;
    }
    
    // Validate name fields
    if (!first_name.trim() || !last_name.trim() || !email.trim()) {
        showToast("Registration Error", "Please fill in all required fields.", "error");
        return;
    }
    
    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px;"></i> Working...';
    lucide.createIcons();
    if (msg) msg.textContent = '';
    
    try {
        const res = await fetch(`${API}/auth/register`, {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({first_name, last_name, email, password})
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Registration Successful", data.message, "success");
            // Store user data for verification step
            localStorage.setItem('temp_email', email);
            localStorage.setItem('temp_password', password);
            localStorage.setItem('temp_first_name', first_name);
            localStorage.setItem('temp_last_name', last_name);
            setTimeout(() => switchAuth('verify'), 1500);
        } else {
            showToast("Registration Failed", data.error, "error");
        }
    } catch (e) {
        showToast("Server Error", "Could not connect to the server. Please check your connection.", "error");
    } finally {
        btn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

async function verifyEmail() {
    const code = document.getElementById('verify-code').value;
    const email = localStorage.getItem('temp_email');
    const msg = document.getElementById('verify-msg');
    const btn = document.querySelector('#auth-verify .btn-submit');
    
    if (!code) {
        showToast("Verification Error", "Please enter the verification code.", "error");
        return;
    }

    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px;"></i> Verifying...';
    lucide.createIcons();
    if (msg) msg.textContent = '';
    
    try {
        const res = await fetch(`${API}/auth/verify-email`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, code})
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Verification Successful", data.message, "success");
            setTimeout(() => switchAuth('login'), 1500);
        } else {
            showToast("Verification Failed", data.error, "error");
        }
    } catch (e) {
        showToast("Server Error", "Could not connect to the server.", "error");
    } finally {
        btn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const msg = document.getElementById('login-msg');
    const btn = document.querySelector('#auth-login .btn-submit');
    
    if (!email || !password) {
        showToast("Login Error", "Please enter your email and password.", "error");
        return;
    }

    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px;"></i> Checking...';
    lucide.createIcons();
    if (msg) msg.textContent = '';

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            if (!data.user.first_name) {
                // If profile incomplete, redirect to profile or show profile setup
                window.location.href = 'profile';
            } else {
                window.location.href = 'dashboard';
            }
        } else {
            showToast("Login Failed", data.error || "Unknown error", "error");
        }
    } catch (e) {
        showToast("Server Error", "Could not connect to the server. Please ensure your backend is running.", "error");
    } finally {
        btn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

async function completeProfile() {
    const first_name = document.getElementById('prof-first-name').value;
    const last_name = document.getElementById('prof-last-name').value;
    const age = document.getElementById('prof-age').value;
    const degree = document.getElementById('prof-degree').value;
    const msg = document.getElementById('prof-msg');
    
    try {
        const res = await fetch(`${API}/auth/profile`, {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({first_name, last_name, age, degree})
        });
        const data = await res.json();
        if (res.ok) {
            let u = JSON.parse(localStorage.getItem('user'));
            u.first_name = data.user.first_name;
            u.last_name = data.user.last_name;
            u.degree = data.user.degree;
            localStorage.setItem('user', JSON.stringify(u));
            currentUser = u;
            initApp();
        } else {
            msg.textContent = data.error;
        }
    } catch (e) {
        msg.textContent = 'Server error.';
    }
}

async function forgotPassword() {
    const email = document.getElementById('forgot-email').value;
    const msg = document.getElementById('forgot-msg');
    const btn = document.querySelector('#auth-forgot .btn-submit');
    
    if(!email) {
        showToast("Input Error", "Please enter your email address.", "error");
        return;
    }

    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px;"></i> Processing...';
    lucide.createIcons();
    if (msg) msg.textContent = '';

    try {
        const res = await fetch(`${API}/auth/forget-password`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email})
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('temp_email', email);
            showToast("Success", "Reset code sent to your email.", "success");
            switchAuth('reset');
        } else {
            showToast("Error", data.error, "error");
        }
    } catch (e) {
        showToast("Server Error", "Could not connect to the server.", "error");
    } finally {
        btn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

async function resetPassword() {
    const email = localStorage.getItem('temp_email');
    const code = document.getElementById('reset-code').value;
    const pass = document.getElementById('reset-password-input').value;
    const conf = document.getElementById('reset-password-confirm').value;
    const msg = document.getElementById('reset-msg');
    const btn = document.querySelector('#auth-reset .btn-submit');

    if(!code) {
        showToast("Input Error", "Please enter the verification code.", "error");
        return;
    }
    if(!pass) { showToast("Security Error", "Please enter a new password.", "error"); return; }
    if(pass !== conf) { showToast("Security Error", "Passwords do not match. Please verify.", "error"); return; }

    const originalBtnHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px;"></i> Updating...';
    lucide.createIcons();
    if (msg) msg.textContent = '';

    try {
        const res = await fetch(`${API}/auth/reset-password`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, code, new_password: pass})
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Success", "Password updated! Redirecting to login...", "success");
            setTimeout(() => switchAuth('login'), 2000);
        } else {
            showToast("Error", data.error, "error");
        }
    } catch (e) { 
        showToast("Server Error", "Could not connect to the server.", "error");
    } finally {
        btn.innerHTML = originalBtnHTML;
        lucide.createIcons();
    }
}

// ── Profile ──────────────────────────────────
function loadProfileData() {
    if(!currentUser) return;
    document.getElementById('profile-full-name').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('profile-email-text').textContent = currentUser.email;
    document.getElementById('profile-degree-text').textContent = currentUser.degree || "Not Set";
    document.getElementById('profile-exam-text').textContent = `${currentUser.exam_target || 'CSS'} Aspirant`;
    
    document.getElementById('prof-edit-first').value = currentUser.first_name;
    document.getElementById('prof-edit-last').value = currentUser.last_name;
    document.getElementById('prof-edit-degree').value = currentUser.degree || "";
    
    const photoImg = document.getElementById('profile-photo-img');
    const sidebarPhoto = document.getElementById('sidebar-user-photo');
    const photoUrl = currentUser.photo_url ? currentUser.photo_url : `https://ui-avatars.com/api/?name=${currentUser.first_name}+${currentUser.last_name}&background=random`;
    
    if(photoImg) photoImg.src = photoUrl;
    if(sidebarPhoto) sidebarPhoto.src = photoUrl;
}

async function uploadProfilePhoto(input) {
    if (!input.files || !input.files[0]) return;
    const formData = new FormData();
    formData.append('photo', input.files[0]);
    
    try {
        const res = await fetch(`${API}/auth/profile/photo`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            currentUser.photo_url = data.photo_url;
            localStorage.setItem('user', JSON.stringify(currentUser));
            loadProfileData();
            showToast("Profile Updated", "Your new profile photo has been successfully uploaded and synced.", "success");
        }
    } catch (e) { showToast("Upload Failed", "Could not upload the image. Please ensure the file is an image and try again.", "error"); }
}

async function saveProfileChanges() {
    const first_name = document.getElementById('prof-edit-first').value;
    const last_name = document.getElementById('prof-edit-last').value;
    const degree = document.getElementById('prof-edit-degree').value;
    const msg = document.getElementById('profile-msg');

    try {
        const res = await fetch(`${API}/auth/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({first_name, last_name, degree})
        });
        const data = await res.json();
        if (res.ok) {
            currentUser.first_name = first_name;
            currentUser.last_name = last_name;
            currentUser.degree = degree;
            localStorage.setItem('user', JSON.stringify(currentUser));
            loadProfileData();
            initApp();
            msg.className = "auth-msg success";
            msg.textContent = "Profile updated successfully!";
            setTimeout(() => msg.textContent = "", 3000);
        }
    } catch (e) {}
}

async function changePasswordFromProfile() {
    const pass = document.getElementById('prof-new-password').value;
    const conf = document.getElementById('prof-confirm-password').value;
    const msg = document.getElementById('profile-msg');

    if(!pass) { showToast("Security Error", "Please enter a new password.", "error"); return; }
    if(pass !== conf) { showToast("Security Error", "Passwords do not match.", "error"); return; }

    try {
        const res = await fetch(`${API}/auth/reset-password`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: currentUser.email, code: "DIRECT", new_password: pass})
        });
        if(res.ok) {
            msg.className = "auth-msg success";
            msg.textContent = "Password changed successfully!";
            document.getElementById('prof-new-password').value = "";
            document.getElementById('prof-confirm-password').value = "";
        }
    } catch (e) {}
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login';
}

// ── Section Navigation ──────────────────────
function initPageSpecifics() {
    const path = window.location.pathname;
    if (path.includes('syllabus-tracker')) loadTracker();
    if (path.includes('preparation')) loadPrepOptions();
    if (path.includes('mock-tests')) loadMockSubjects();
    if (path.includes('past-papers-repo')) loadPastPapers();
    if (path.includes('dashboard')) loadDashboardDetails();
    if (path.includes('profile')) loadProfileData();
}

function showSection(sectionId, clickedEl) {
    console.log("Navigating to section:", sectionId);
    const pages = {
        'dashboard': 'dashboard',
        'preparation': 'preparation',
        'tracker': 'syllabus-tracker',
        'mocktest': 'mock-tests',
        'essay': 'essay-studio',
        'evaluator': 'answer-evaluator',
        'pastpapers': 'past-papers-repo',
        'profile': 'profile'
    };
    if (pages[sectionId]) {
        window.location.href = pages[sectionId];
    }
}

// ── Prep Setup ─────────────────────────────
let patternData = {};
let currentPrep = null;

async function deletePreparation() {
    const confirmed = await showConfirm("Delete Progress?", "Are you sure you want to delete your current preparation? This will reset your syllabus tracker and all progress.", "Delete Everything");
    if (!confirmed) return;
    
    try {
        const res = await fetch(`${API}/prep/status/delete`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if(res.ok) {
            currentPrep = null;
            location.reload();
        }
    } catch(e){}
}

async function loadPrepOptions() {
    try {
        const res = await fetch(`${API}/prep/patterns`);
        if(res.ok) {
            patternData = await res.json();
        }
        
        const statusRes = await fetch(`${API}/prep/status`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (statusRes.ok) {
            currentPrep = await statusRes.json();
            if (currentPrep.exam_target) {
                document.getElementById('exam-target').value = currentPrep.exam_target;
                handleExamChange();
                
                if (currentPrep.province) document.getElementById('exam-province').value = currentPrep.province;
                if (currentPrep.exam_date) document.getElementById('exam-date').value = currentPrep.exam_date;
                
                renderSubjects();
                
                document.getElementById('save-prep-btn').textContent = 'Update Preparation & Schedule';
                document.getElementById('delete-prep-btn').classList.remove('hidden');
                
                const msg = document.getElementById('prep-status-msg');
                msg.style.display = 'block';
                msg.className = 'auth-msg success';
                msg.textContent = `Active Preparation: ${currentPrep.exam_target} ${currentPrep.province || ''}. You can update your date or optional subjects below.`;
            } else {
                document.getElementById('save-prep-btn').textContent = 'Generate Syllabus Tracker';
                document.getElementById('delete-prep-btn').classList.add('hidden');
                document.getElementById('prep-status-msg').style.display = 'none';
            }
        }
    } catch(e) {}
}

function handleExamChange() {
    const exam = document.getElementById('exam-target').value;
    const provContainer = document.getElementById('province-container');
    if (exam === 'PMS') {
        provContainer.classList.remove('hidden');
    } else {
        provContainer.classList.add('hidden');
    }
    renderSubjects();
}

function renderSubjects() {
    const exam = document.getElementById('exam-target').value;
    const province = document.getElementById('exam-province').value;
    const compContainer = document.getElementById('compulsory-container');
    const optContainer = document.getElementById('optional-container');
    const compList = document.getElementById('compulsory-list');
    const optGroups = document.getElementById('optional-groups');
    
    compList.innerHTML = '';
    optGroups.innerHTML = '';
    
    if (!exam || (exam === 'PMS' && !province)) {
        compContainer.classList.add('hidden');
        optContainer.classList.add('hidden');
        return;
    }
    
    let comp = [];
    let optGroupsData = [];
    
    if (exam === 'CSS' && patternData.CSS) {
        comp = patternData.CSS.compulsory_subjects || [];
        optGroupsData = patternData.CSS.optional_subjects?.groups || [];
    } else if (exam === 'PMS' && patternData.PMS && patternData.PMS[province]) {
        comp = patternData.PMS[province].compulsory_subjects || [];
        optGroupsData = patternData.PMS[province].optional_subjects?.groups || [];
    } else if (exam === 'PPSC' && patternData.PPSC) {
        // For PPSC, treat sections as compulsory topics
        comp = patternData.PPSC.sections || [];
        optGroupsData = [];
    }
    
    if (comp.length > 0) {
        compList.innerHTML = comp.map(s => `<li><label><input type="checkbox" checked disabled> <b>${s.name}</b></label></li>`).join('');
        compContainer.classList.remove('hidden');
    }
    
    if (optGroupsData.length > 0) {
        let optHtml = `<div id="selection-status" style="margin-bottom: 15px; font-size: 1.1em; color: #9ca3af;"></div>`;
        optGroupsData.forEach((g, idx) => {
            let limit = 1;
            if (exam === 'CSS' && g.instruction.toLowerCase().includes('two')) limit = 2;
            let marks = 100;
            if (exam === 'CSS' && g.name.includes('200')) marks = 200;
            
            optHtml += `<div class="opt-group" style="margin-bottom:15px; padding: 10px; background: var(--gray-50); border-radius: 8px; border: 1px solid var(--gray-200);">
                <h4 style="margin-bottom:8px; margin-top:0; color:#60a5fa;">${g.name} <span style="font-size:0.85em; font-weight:normal; color:#9ca3af;">(${g.instruction})</span></h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">`;
            g.subjects.forEach(s => {
                const isChecked = currentPrep && currentPrep.subjects && currentPrep.subjects.some(cs => cs.subject_id === s.id);
                optHtml += `<label><input type="checkbox" class="opt-subject" value="${s.id}" data-group="${idx}" data-group-limit="${limit}" data-marks="${marks}" onchange="updateValidation()" ${isChecked ? 'checked' : ''}> ${s.name}</label>`;
            });
            optHtml += `</div></div>`;
        });
        optGroups.innerHTML = optHtml;
        optContainer.classList.remove('hidden');
        updateValidation();
    }
}

function updateValidation() {
    const exam = document.getElementById('exam-target').value;
    const checkboxes = Array.from(document.querySelectorAll('.opt-subject'));
    let totalMarks = 0;
    let totalSubjects = 0;
    let groupCounts = {};
    checkboxes.forEach(cb => {
        if (cb.checked) {
            let group = cb.getAttribute('data-group');
            groupCounts[group] = (groupCounts[group] || 0) + 1;
            totalMarks += parseInt(cb.getAttribute('data-marks') || 0);
            totalSubjects++;
        }
    });

    checkboxes.forEach(cb => {
        let group = cb.getAttribute('data-group');
        let groupLimit = parseInt(cb.getAttribute('data-group-limit'));
        let isGroupFull = (groupCounts[group] || 0) >= groupLimit;
        let isTotalFull = false;
        if (exam === 'CSS') isTotalFull = (totalMarks + parseInt(cb.getAttribute('data-marks') || 0) > 600);
        else if (exam === 'PMS') isTotalFull = (totalSubjects >= 3);

        if (!cb.checked) {
            cb.disabled = isGroupFull || isTotalFull;
            cb.parentElement.style.opacity = cb.disabled ? '0.4' : '1';
        }
    });
    
    const statusDiv = document.getElementById('selection-status');
    if (statusDiv) {
        if (exam === 'CSS') statusDiv.innerHTML = `Selection Status: <b>${totalMarks} / 600 Marks</b>`;
        else if (exam === 'PMS') statusDiv.innerHTML = `Selection Status: <b>${totalSubjects} / 3 Subjects</b>`;
    }
}

async function savePreparation() {
    const exam_target = document.getElementById('exam-target').value;
    const province = document.getElementById('exam-province').value;
    const exam_date = document.getElementById('exam-date').value;
    const optional_subjects = Array.from(document.querySelectorAll('.opt-subject:checked')).map(i => i.value);
    
    if (!exam_target || !exam_date) {
        showToast("Incomplete Setup", "Please select your target exam and date before generating the schedule.", "error");
        return;
    }
    
    // Validate optional subjects for PMS only (PPSC is MCQ-only)
    if (exam_target === 'PMS' && optional_subjects.length < 3) {
        showToast("Missing Subjects", `PMS requires 3 optional subjects. You selected ${optional_subjects.length}.`, "error");
        return;
    }
    
    const btn = document.getElementById('save-prep-btn');
    btn.textContent = 'Generating Schedule...';
    btn.disabled = true;
    
    try {
        const res = await fetch(`${API}/prep/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({exam_target, province, exam_date, optional_subjects})
        });
        const data = await res.json();
        if (res.ok) {
            // Update local user object to reflect navigation changes immediately
            const user = JSON.parse(localStorage.getItem('user'));
            if (user) {
                user.exam_target = exam_target;
                localStorage.setItem('user', JSON.stringify(user));
            }
            
            // Refresh sidebar to show/hide context-specific tabs
            if (typeof injectSidebar === 'function') injectSidebar();

            loadTracker();
            showSection('tracker', document.getElementById('nav-tracker'));
            showToast("Success", "Your preparation schedule has been generated!", "success");
        } else {
            showToast("Error", data.error || "Failed to save preparation", "error");
            btn.textContent = exam_target === 'CSS' ? 'Generate Syllabus Tracker' : 'Update Preparation & Schedule';
            btn.disabled = false;
        }
    } catch (e) {
        showToast("Error", "Network error while saving preparation", "error");
        btn.textContent = exam_target === 'CSS' ? 'Generate Syllabus Tracker' : 'Update Preparation & Schedule';
        btn.disabled = false;
    }
}

// ── Tracker Dashboard ─────────────────────────
async function loadTracker() {
    try {
        const res = await fetch(`${API}/prep/schedule`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        const container = document.getElementById('tracker-content');
        if (data.tasks && data.tasks.length > 0) {
            const subjects = {};
            let completed = 0;
            data.tasks.forEach(t => {
                if (!subjects[t.subject_id]) subjects[t.subject_id] = { tasks: [], done: 0 };
                subjects[t.subject_id].tasks.push(t);
                if (t.is_completed) { subjects[t.subject_id].done++; completed++; }
            });

            let html = '<div class="tracker-list">';
            for (const subjId in subjects) {
                const s = subjects[subjId];
                const pct = (s.done / s.tasks.length) * 100;
                html += `
                <div class="tracker-subject-card">
                    <div class="tracker-subject-header">
                        <h3><i data-lucide="book" class="icon-inline"></i> ${subjId}</h3>
                        <div class="d-flex align-items-center gap-3">
                            <span class="meta">${s.done}/${s.tasks.length}</span>
                            <div class="tracker-progress-bar"><div class="tracker-progress-fill" style="width: ${pct}%"></div></div>
                        </div>
                    </div>
                    <div class="tracker-subject-body">
                        ${s.tasks.map(t => `
                            <div class="topic-row">
                                <div class="topic-info">
                                    <input type="checkbox" ${t.is_completed?'checked':''} onchange="toggleTask(${t.id}, this.checked)">
                                    <span style="${t.is_completed?'text-decoration: line-through; color: var(--text-muted)':''}">${t.topic_name}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>`;
            }
            container.innerHTML = html + '</div>';
            lucide.createIcons();
            // Update Dash
            let overallPct = (completed / data.tasks.length) * 100;
            const progressText = document.getElementById('progress-text');
            if (progressText) progressText.textContent = `${Math.round(overallPct)}% Syllabus covered`;
            updateProgressChart(overallPct);
            
            const examDate = new Date(data.tasks[data.tasks.length-1].date_assigned);
            const diff = Math.ceil((examDate - new Date()) / (1000 * 60 * 60 * 24));
            const countdownEl = document.getElementById('exam-countdown');
            if (countdownEl) countdownEl.textContent = diff > 0 ? diff : 0;
            
            const targetTextEl = document.getElementById('exam-target-text');
            if (targetTextEl) targetTextEl.textContent = "Days Left until Exam Completion";
            
            loadDashboardDetails();
        }
    } catch (e) {}
}

async function toggleTask(id, is_completed) {
    try {
        await fetch(`${API}/prep/task/${id}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({is_completed})
        });
        loadTracker();
    } catch(e){}
}

// ── Mock Test ──────────────────────────────
let userMockSubjects = [];
async function loadMockSubjects() {
    try {
        const res = await fetch(`${API}/mocktest/subjects`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        userMockSubjects = await res.json();
        const select = document.getElementById('mock-subject');
        if (userMockSubjects.length > 0) {
            select.innerHTML = userMockSubjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
            updateMockTypeOptions(); // Initial update
        }
    } catch(e){}
}

function updateMockTypeOptions() {
    const subjId = document.getElementById('mock-subject').value;
    const typeSelect = document.getElementById('mock-type');
    if(!typeSelect) return;
    const subj = userMockSubjects.find(s => s.id === subjId);
    
    if(!subj) return;
    
    let options = '';
    // Special case for PPSC Mix Paper
    if(subj.id === 'ppsc_mix_paper') {
        options = `<option value="objective">Generate Full Mix Paper (All Sections)</option>`;
    } else if(subj.id.toLowerCase().includes('essay') || subj.id.toLowerCase().includes('precis')) {
        options = `<option value="subjective">Subjective Only</option>`;
    } else if(subj.type === 'mixed_objective_subjective') {
        options = `
            <option value="all">Full Paper (Mixed)</option>
            <option value="objective">Objective Only (MCQs)</option>
            <option value="subjective">Subjective Only</option>
        `;
    } else if(subj.type === 'subjective_only') {
        options = `<option value="subjective">Subjective Only</option>`;
    } else if(subj.type === 'objective_only') {
        options = `<option value="objective">Objective Only (MCQs)</option>`;
    }
    
    typeSelect.innerHTML = options;
}

function switchMockView(view, btn) {
    document.querySelectorAll('.mock-view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(`mock-${view}-view`);
    if(target) target.classList.remove('hidden');
    
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if(btn) btn.classList.add('active');

    lucide.createIcons();
    if(view === 'history') loadMockHistory();
    if(view === 'pending') loadPendingEvaluations();
}

async function generateMockTest() {
    const subject = document.getElementById('mock-subject').value;
    const type = document.getElementById('mock-type').value;
    if(!subject) {
        showToast("Missing Selection", "Please select a subject before starting the exam hall.", "error");
        return;
    }
    
    try {
        const res = await fetch(`${API}/mocktest/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ subject_id: subject, paper_type: type })
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('activeExam', JSON.stringify(data));
            // Redirect to the Exam Hall in the SAME tab
            window.location.href = 'exam-hall';
        } else {
            showToast("Generation Failed", data.error || "The server encountered a problem while curating your paper.", "error");
        }
    } catch (e) { 
        showToast("Network Error", "Could not establish a connection to the exam server.", "error");
    }
}

// ── Exam Hall Logic ─────────────────────────
let examTimer = null;
let examTimeLeft = 0;

async function initExamHall() {
    const data = JSON.parse(localStorage.getItem('activeExam'));
    if (!data) {
        window.location.href = 'dashboard';
        return;
    }
    activeTest = data;
    document.getElementById('exam-subject-title').innerText = activeTest.subject_name;
    examTimeLeft = activeTest.total_time * 60;
    
    renderExamQuestions();
    startExamTimer();
}

function startExamTimer() {
    const display = document.getElementById('exam-timer-display');
    examTimer = setInterval(() => {
        const mins = Math.floor(examTimeLeft / 60);
        const secs = examTimeLeft % 60;
        display.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        
        if (examTimeLeft <= 0) {
            clearInterval(examTimer);
            submitMockTest(true); // Auto-submit
        }
        examTimeLeft--;
    }, 1000);
}

function renderExamQuestions() {
    const container = document.getElementById('exam-questions-container');
    let html = "";
    
    activeTest.sections.forEach(section => {
        html += `<div class="section-divider mt-5 mb-4">
                    <h3 class="section-title-premium">${section.title}</h3>
                    <span class="badge-premium">${section.marks} Marks Total</span>
                 </div>`;
                 
        section.questions.forEach((q, i) => {
            if (section.type === 'objective') {
                html += `
                <div class="glass-card card p-4 mb-4 question-card">
                    <div class="question-text">Q${i+1}: ${q.text}</div>
                    <div class="options-container">
                        ${q.options.map((opt, optIdx) => `
                            <label class="option-item">
                                <input type="radio" name="q${q.id}" value="${opt}">
                                <div class="option-box">
                                    <span class="option-letter">${String.fromCharCode(65 + optIdx)}</span>
                                    <span class="option-content">${opt}</span>
                                </div>
                            </label>
                        `).join('')}
                    </div>
                </div>`;
            } else {
                html += `
                <div class="glass-card card p-4 mb-4 question-card">
                    <div class="question-text">Q${i+1}: ${q.text} <span class="meta-inline">(${q.marks} Marks)</span></div>
                    <textarea id="sub-q-${q.id}" class="subjective-area" placeholder="Write your comprehensive answer here..." rows="10"></textarea>
                </div>`;
            }
        });
    });
    
    container.innerHTML = html;
    lucide.createIcons();
}

async function submitMockTest(isAuto = false) {
    if (!activeTest) return;
    
    const user_answers = {};
    let score_objective = 0;

    activeTest.sections.forEach(section => {
        section.questions.forEach((q) => {
            if (section.type === 'objective') {
                const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
                const val = selected ? selected.value : "";
                user_answers[q.id] = val;
                if (val === q.correct) score_objective += (section.marks / section.questions.length);
            } else {
                const area = document.getElementById(`sub-q-${q.id}`);
                user_answers[q.id] = area ? area.value : "";
            }
        });
    });

    try {
        const res = await fetch(`${API}/mocktest/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ 
                test_id: activeTest.test_id, 
                user_answers,
                score_objective: Math.round(score_objective)
            })
        });
        
        if (res.ok) {
            clearInterval(examTimer);
            localStorage.removeItem('activeExam'); // Clear active test
            if (isAuto) {
                showToast("Time's Up!", "Your paper was automatically submitted.", "warning");
            } else {
                showToast("Exam Submitted", "Your responses have been securely recorded.", "success");
            }
            window.location.href = 'dashboard';
        }
    } catch (e) {
        showToast("Submission Error", "Failed to reach the server. Please check your connection.", "error");
    }
}

function renderMockPaper() {
    const resDiv = document.getElementById('mock-result');
    if(!activeTest || !activeTest.sections) {
        resDiv.innerHTML = '<p class="error">Invalid paper structure received.</p>';
        return;
    }

    let html = `<div class="mock-paper card">
        <div class="mock-paper-header">
            <h3>${activeTest.subject_name}</h3>
            <p class="meta">${activeTest.type.toUpperCase()} PAPER — Time Limit: ${activeTest.total_time} mins</p>
        </div>
        <div class="mock-questions">`;
    
    activeTest.sections.forEach(section => {
        html += `<div class="section-title mt-4"><h4>${section.title} (${section.marks} Marks)</h4></div>`;
        
        section.questions.forEach((q, i) => {
            if(section.type === 'objective') {
                html += `<div class="q-block">
                    <p><b>Q${i+1}:</b> ${q.text}</p>
                    <div class="options-grid">
                        ${q.options.map((opt) => `
                            <label class="option-label">
                                <input type="radio" name="q${i}" value="${opt}"> ${opt}
                            </label>
                        `).join('')}
                    </div>
                </div>`;
            } else {
                html += `<div class="q-block">
                    <p><b>Q${i+1}:</b> ${q.text} <span class="meta">(${q.marks} Marks)</span></p>
                    <textarea id="sub-q-${q.id}" class="mt-2" placeholder="Type your detailed answer here..." rows="6"></textarea>
                </div>`;
            }
        });
    });
    
    html += `</div><button onclick="submitMockTest()" class="mt-4 w-100">Submit Finished Paper <i data-lucide="check-circle"></i></button></div>`;
    resDiv.innerHTML = html;
    lucide.createIcons();
}

async function loadMockHistory() {
    const container = document.getElementById('mock-history-list');
    if(!container) return;
    try {
        const res = await fetch(`${API}/mocktest/history`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        if (res.ok && data.length > 0) {
            container.innerHTML = data.map(m => {
                const dateObj = new Date(m.created_at);
                const dateStr = dateObj.toLocaleDateString() + " " + dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                const totalScore = (m.score_objective || 0) + (m.score_subjective || 0);
                const status = m.is_evaluated ? 'Evaluated' : 'Objective Only';
                
                return `
                <div class="history-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <b>${m.subject_name}</b> <br>
                            <small class="meta">${dateStr} • ${status}</small>
                        </div>
                        <div class="text-right">
                            <span class="status-pill status-completed">Total Score: ${totalScore}</span>
                            <br>
                            <button class="btn-sm mt-2" onclick="viewMockResult(${m.id})">Show Paper <i data-lucide="eye" style="width:12px;"></i></button>
                        </div>
                    </div>
                </div>
            `}).join('');
            lucide.createIcons();
        } else {
            container.innerHTML = '<p class="placeholder">You have no completed mock tests in your history.</p>';
        }
    } catch(e){
        container.innerHTML = '<p class="placeholder" style="color:var(--error)">⚠️ Could not sync history from the server.</p>';
    }
}

async function loadPendingEvaluations() {
    const container = document.getElementById('mock-pending-list'); // Fixed ID from pending-evaluations to mock-pending-list
    if(!container) return;
    try {
        const res = await fetch(`${API}/mocktest/pending`, { 
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        if (data.length > 0) {
            container.innerHTML = data.map(m => {
                const date = new Date(m.created_at).toLocaleDateString();
                return `
                <div class="history-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <b>${m.subject_name}</b> <br>
                            <small class="meta">Taken on ${date} • Waiting for AI Review</small>
                        </div>
                        <button class="btn-sm" onclick="openEvaluation(${m.id})">Evaluate with AI Expert</button>
                    </div>
                </div>
            `}).join('');
        } else {
            container.innerHTML = '<p class="placeholder">No pending subjective papers.</p>';
        }
    } catch(e){}
}

function openEvaluation(testId) {
    document.getElementById('evaluation-overlay').classList.remove('hidden');
    const content = document.getElementById('evaluation-content');
    content.innerHTML = `
        <h3>Subjective Evaluation</h3>
        <p>Your answer is being analyzed by the CSS/PMS AI Expert Mentor.</p>
        <button onclick="evaluateWithAI(${testId})" class="w-100">Start AI Evaluation</button>
    `;
}

async function evaluateWithAI(testId) {
    const content = document.getElementById('evaluation-content');
    content.innerHTML = '<p class="loading">⏳ AI Examiner is checking your answers... This may take a minute.</p>';
    
    try {
        const res = await fetch(`${API}/mocktest/evaluate-ai`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ test_id: testId })
        });
        const data = await res.json();
        
        if (res.ok) {
            if(data.results) {
                let html = `<h2 style="color:var(--primary); margin-bottom: 20px; text-align: center; border-bottom: 2px solid var(--gray-200); padding-bottom: 15px;">Official CSS/PMS Academic Transcript</h2>`;
                data.results.forEach(r => {
                    html += `
                        <div class="eval-block mb-5">
                            <div class="q-header p-3" style="background: var(--gray-100); border-radius: 8px 8px 0 0; border-bottom: 2px solid var(--primary);">
                                <b>QUESTION:</b> ${r.question_text}
                            </div>
                            <div class="eval-body p-4" style="background: white; border: 1px solid var(--gray-200); border-top: none; border-radius: 0 0 8px 8px;">
                                ${r.evaluation}
                            </div>
                        </div>`;
                });
                html += `<div class="text-center mt-5"><button onclick="closeEvaluation()" class="btn-primary" style="padding: 12px 40px;">Close Official Report</button></div>`;
                content.innerHTML = html;
            } else {
                content.innerHTML = `<div class="p-4 text-center">${data.message || "Evaluation complete!"}</div>`;
            }
        } else {
            content.innerHTML = `<p class="error">${data.error}</p>`;
        }
    } catch(e) {
        content.innerHTML = `<p class="error">Server error during evaluation.</p>`;
    }
}

async function viewMockResult(testId) {
    window.open(`view-results.html?testId=${testId}`, '_blank');
}

function closeEvaluation() {
    document.getElementById('evaluation-overlay').classList.add('hidden');
    loadMockHistory();
    loadPendingEvaluations();
}



async function generateEssay() {
    const topic = document.getElementById('essay-topic').value;
    const resDiv = document.getElementById('essay-result');
    if(!topic) return;
    
    resDiv.innerHTML = '<p class="loading">⏳ Architecting essay structure and gathering data... (Step 1/2)</p>';
    try {
        const res = await fetch(`${API}/generate-essay`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic})
        });
        const data = await res.json();
        if(res.ok) {
            // Convert markdown style headers to HTML
            let html = data.content
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/\n/g, '<br>');
            resDiv.innerHTML = `<div class="p-3">${html}</div>`;
        } else {
            resDiv.innerHTML = `<p class="error">${data.error}</p>`;
        }
    } catch(e) {
        resDiv.innerHTML = `<p class="error">Generation failed. Is Ollama running?</p>`;    }
}

async function evaluateAnswer() {
    const question = document.getElementById('eval-question').value;
    const answer = document.getElementById('eval-answer').value;
    const resDiv = document.getElementById('eval-result');
    if(!question || !answer) return;

    resDiv.innerHTML = '<p class="loading">⏳ Expert Mentor is reviewing your draft... (Using Mistral Local)</p>';
    try {
        const res = await fetch(`${API}/evaluate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question, answer})
        });
        const data = await res.json();
        if(res.ok) {
            resDiv.innerHTML = `<div class="p-3">${data.evaluation}</div>`;
        } else {
            resDiv.innerHTML = `<p class="error">${data.error}</p>`;
        }
    } catch(e) {
        resDiv.innerHTML = `<p class="error">Evaluation failed.</p>`;
    }
}

// ── Other Functions ─────────────────────────
let progressChartInstance = null;
function updateProgressChart(pct) {
    const canvas = document.getElementById('progressChart');
    if (!canvas) return;
    if (typeof Chart === 'undefined') {
        console.warn("Chart.js not loaded yet.");
        return;
    }
    const ctx = canvas.getContext('2d');
    if (progressChartInstance) progressChartInstance.destroy();
    progressChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [pct, 100 - pct], backgroundColor: ['#581c87', '#e5e7eb'], borderWidth: 0 }] },
        options: { cutout: '80%', responsive: true, maintainAspectRatio: false, plugins: { tooltip: { enabled: false } } }
    });
}

async function loadDashboardDetails() {
    try {
        // 1. Load Tracker Data for Progress & Weak Topics
        const res = await fetch(`${API}/tracker`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        
        // Update Chart & Progress Text
        if (data.overall_completion !== undefined) {
            updateProgressChart(data.overall_completion);
            const progressText = document.getElementById('progress-text');
            if (progressText) progressText.textContent = `${Math.round(data.overall_completion)}% Syllabus covered`;
        }

        // Update Weak Topics
        const weakList = document.getElementById('weak-topics');
        if (weakList) {
            if (data.weak_topics && data.weak_topics.length > 0) {
                weakList.innerHTML = data.weak_topics.map(t => `
                    <li class="history-item" style="border-left: 3px solid #ef4444;">
                        <b>${t.topic}</b> <br>
                        <small style="color:var(--text-muted)">Subject: ${t.subject}</small> <br>
                        <span class="badge" style="background:#fef2f2; color:#ef4444; font-size: 0.7rem;">Needs Review</span>
                    </li>
                `).join('');
            } else {
                weakList.innerHTML = '<p class="placeholder">No weak topics detected yet. Keep up the good work!</p>';
            }
        }

        // 2. Load Schedule for Countdown
        const resSched = await fetch(`${API}/prep/schedule`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const dataSched = await resSched.json();
        if (dataSched.tasks && dataSched.tasks.length > 0) {
            const examDate = new Date(dataSched.tasks[dataSched.tasks.length-1].date_assigned);
            const diff = Math.ceil((examDate - new Date()) / (1000 * 60 * 60 * 24));
            const countdownEl = document.getElementById('exam-countdown');
            if (countdownEl) countdownEl.textContent = diff > 0 ? diff : 0;
            
            const targetTextEl = document.getElementById('exam-target-text');
            if (targetTextEl) targetTextEl.textContent = "Days Left until Exam Completion";
        }
    } catch(e) {
        console.error("Error loading dashboard details:", e);
    }
}

// ── Expert Mentor Chat ──────────────────────
let chatHistory = [];
function toggleChat() {
    const container = document.getElementById('chat-container');
    if(container) container.classList.toggle('hidden');
}
function scrollToBottom() {
    const msgs = document.getElementById('chat-messages');
    if(msgs) msgs.scrollTop = msgs.scrollHeight;
}
async function sendMentorMessage() {
    const input = document.getElementById('chat-input');
    const query = input ? input.value.trim() : "";
    if(!query) return;
    input.value = '';
    appendMessage('user', query);
    const loadingMsg = appendMessage('ai', '⏳ Mentor is thinking...');
    try {
        const res = await fetch(`${API}/mentor/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query, history: chatHistory})
        });
        const data = await res.json();
        if(loadingMsg) loadingMsg.remove();
        if(res.ok) {
            appendMessage('ai', data.answer);
            chatHistory.push({role: 'user', content: query}, {role: 'assistant', content: data.answer});
            if(chatHistory.length > 10) chatHistory.splice(0, 2);
        }
    } catch(e) { if(loadingMsg) loadingMsg.remove(); }
    scrollToBottom();
}
function appendMessage(role, text) {
    const msgs = document.getElementById('chat-messages');
    if(!msgs) return;
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = text;
    msgs.appendChild(div);
    scrollToBottom();
    return div;
}

// ── Past Papers Logic ───────────────────────
let allPastPapers = [];
async function loadPastPapers() {
    const grid = document.getElementById('past-papers-grid');
    if(!grid) return;
    
    try {
        let examTarget = null;
        if (localStorage.getItem('token')) {
            try {
                const statusRes = await fetch(`${API}/prep/status`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                if (statusRes.ok) {
                    const prep = await statusRes.json();
                    examTarget = prep.exam_target;
                }
            } catch (e) {}
        }

        let url = `${API}/past-papers`;
        if (examTarget) {
            url += `?exam_type=${examTarget}`;
            const titleEl = document.getElementById('past-papers-title');
            if (titleEl) {
                titleEl.innerHTML = `<i data-lucide="archive" class="icon-inline"></i> ${examTarget} Past Papers Repository`;
                lucide.createIcons();
            }
        }
        const res = await fetch(url);
        const data = await res.json();
        allPastPapers = data;
        
        // Populate Year Filter
        const years = [...new Set(data.map(p => p.year))].sort((a,b) => b-a);
        const yearFilter = document.getElementById('paper-year-filter');
        if(yearFilter && yearFilter.options.length <= 1) {
            years.forEach(y => {
                if(y !== "Unknown") {
                    const opt = document.createElement('option');
                    opt.value = y;
                    opt.innerText = y;
                    yearFilter.appendChild(opt);
                }
            });
        }
        
        renderPaperGrid(allPastPapers);
    } catch(e) {
        grid.innerHTML = '<p class="error">Failed to load paper repository.</p>';
    }
}

function renderPaperGrid(papers) {
    const grid = document.getElementById('past-papers-grid');
    if(papers.length === 0) {
        grid.innerHTML = '<p class="placeholder">No papers found matching your criteria.</p>';
        return;
    }
    
    grid.innerHTML = papers.map(p => `
        <div class="card p-3 d-flex flex-column justify-content-between" style="border-left: 4px solid var(--primary); transition: 0.3s; height: 160px;">
            <div>
                <div class="d-flex justify-content-between">
                    <div>
                        <span class="badge" style="background: var(--primary-light); color: var(--primary); font-size: 0.7rem;">${p.year}</span>
                        ${p.exam_type ? `<span class="badge" style="background: var(--gray-200); color: var(--gray-700); font-size: 0.7rem; margin-left: 5px;">${p.exam_type}</span>` : ''}
                    </div>
                    <i data-lucide="file-text" style="width: 16px; color: var(--text-muted);"></i>
                </div>
                <h4 class="mt-2 mb-1" style="font-size: 1rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${p.subject}</h4>
            </div>
            <button class="btn-sm w-100" onclick="window.open('${API}/past-papers/view/${encodeURIComponent(p.filename)}', '_blank')">
                View PDF <i data-lucide="external-link" style="width:12px;"></i>
            </button>
        </div>
    `).join('');
    lucide.createIcons();
}

function filterPastPapers() {
    const query = document.getElementById('paper-search').value.toLowerCase();
    const year = document.getElementById('paper-year-filter').value;
    
    const filtered = allPastPapers.filter(p => {
        const matchesQuery = p.subject.toLowerCase().includes(query) || p.year.includes(query);
        const matchesYear = year === "" || p.year === year;
        return matchesQuery && matchesYear;
    });
    
    renderPaperGrid(filtered);
}

// Final Init
document.addEventListener('DOMContentLoaded', () => {
    const subjSelect = document.getElementById('mock-subject');
    if(subjSelect) {
        subjSelect.addEventListener('change', updateMockTypeOptions);
    }
    initApp();
});
