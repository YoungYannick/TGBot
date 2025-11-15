document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-item a');
    const pages = document.querySelectorAll('.page');
    const pageTitle = document.getElementById('page-title');
    const body = document.body;
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mainContent = document.querySelector('.main-content');
    const dropdownBtn = document.querySelector('.dropdown-btn');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    const themeIcon = document.querySelector('.theme-icon');
    const themeLabel = document.querySelector('.theme-label');
    const customModal = document.getElementById('custom-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const modalConfirmBtn = document.getElementById('modal-confirm-btn');
    const modalCancelBtn = document.getElementById('modal-cancel-btn');

    function customConfirm(title, message, confirmText = '确认', confirmStyle = 'btn-danger') {
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        modalConfirmBtn.textContent = confirmText;
        modalConfirmBtn.className = `btn ${confirmStyle}`;
        customModal.style.display = 'flex';
        return new Promise(resolve => {
            setTimeout(() => {
                customModal.classList.add('show');
            }, 10);
            const transitionEndHandler = (e) => {
                if (e.target !== customModal || e.propertyName !== 'opacity') return;
                if (!customModal.classList.contains('show')) {
                    customModal.style.display = 'none';
                    customModal.removeEventListener('transitionend', transitionEndHandler);
                }
            };
            customModal.addEventListener('transitionend', transitionEndHandler);
            const handleConfirmation = (result) => {
                customModal.classList.remove('show');
                modalConfirmBtn.removeEventListener('click', confirmListener);
                modalCancelBtn.removeEventListener('click', cancelListener);
                resolve(result);
            };
            const confirmListener = () => handleConfirmation(true);
            const cancelListener = () => handleConfirmation(false);
            modalConfirmBtn.addEventListener('click', confirmListener);
            modalCancelBtn.addEventListener('click', cancelListener);
        });
    }

    const state = {
        keywords: {
            list: [],
            currentPage: 1,
            search: '',
            filter: 'all'
        },
        users: {
            currentPage: 1,
            search: '',
            filter: 'all'
        },
        chat: {
            userId: null,
            page: 1,
            search: '',
            start: '',
            end: ''
        },
        sidebarCollapsed: false,
        theme: localStorage.getItem('theme') || 'auto',
        chart: null
    };

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function setTheme(theme) {
        if (theme === 'auto') {
            body.dataset.theme = mediaQuery.matches ? 'dark' : 'light';
        } else {
            body.dataset.theme = theme;
        }
        state.theme = theme;
        localStorage.setItem('theme', theme);
        updateThemeDisplay(theme);
    }

    function updateThemeDisplay(theme) {
        let label = theme.charAt(0).toUpperCase() + theme.slice(1);
        let iconHTML = '';
        if (theme === 'light') {
            iconHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
        } else if (theme === 'dark') {
            iconHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
        } else {
            label = 'Auto';
            iconHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06 .06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82 .33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>';
        }
        themeIcon.innerHTML = iconHTML;
        themeLabel.textContent = label;
    }

    dropdownBtn.addEventListener('click', () => {
        dropdownMenu.classList.toggle('show');
    });

    dropdownMenu.addEventListener('click', (e) => {
        const option = e.target.closest('div[data-theme]');
        if (option) {
            setTheme(option.dataset.theme);
            dropdownMenu.classList.remove('show');
        }
    });

    document.addEventListener('click', (e) => {
        if (!dropdownBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.remove('show');
        }
    });

    mediaQuery.addEventListener('change', () => {
        if (state.theme === 'auto') {
            setTheme('auto');
        }
    });

    setTheme(state.theme);

    function toggleSidebar() {
        state.sidebarCollapsed = !state.sidebarCollapsed;
        sidebar.classList.toggle('collapsed', state.sidebarCollapsed);
        sidebarToggle.textContent = state.sidebarCollapsed ? '>' : '≡';
        if (mainContent) {
            mainContent.style.marginLeft = state.sidebarCollapsed ? '60px' : '200px';
        }
    }

    sidebarToggle.addEventListener('click', toggleSidebar);

    function switchPage(pageId) {
        navLinks.forEach(link => link.classList.remove('active'));
        document.querySelector(`[data-page="${pageId}"]`).classList.add('active');
        pages.forEach(page => {
            page.classList.remove('active');
            if (page.id === `${pageId}-page`) {
                page.style.animation = 'fadeIn 0.3s ease-out';
                page.classList.add('active');
            }
        });
        pageTitle.textContent = {
            dashboard: '仪表盘',
            'bot-settings': '机器人设置',
            'start-message': '欢迎消息',
            users: '用户管理',
            keywords: '屏蔽关键词'
        }[pageId];
        if (pageId === 'dashboard') loadStats();
        if (pageId === 'users') updateUsersAndLoad();
        if (pageId === 'keywords') updateKwAndLoad();
        if (pageId === 'bot-settings') loadBotSettings();
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchPage(link.dataset.page);
        });
    });

    async function apiFetch(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({'error': 'API error'}));
            throw new Error(errorData.error || 'API error');
        }
        return response.json();
    }

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.classList.add('toast', type);
        toast.textContent = message;
        document.getElementById('toast-container').appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    async function loadStats() {
        try {
            const data = await apiFetch('/api/stats');
            document.getElementById('total-users').textContent = data.total_users;
            document.getElementById('blocked-users').textContent = data.blocked_users;
            document.getElementById('verified-users').textContent = data.verified_users;
            document.getElementById('total-keywords').textContent = data.total_keywords;
            const today = await apiFetch('/api/today_stats');
            document.getElementById('new-users-today').textContent = today.new_users_today;
            document.getElementById('dialog-users-today').textContent = today.dialog_users_today;
            document.getElementById('messages-today').textContent = today.messages_today;
            loadStartMessages();

            const rangeSelect = document.getElementById('range-select');
            loadMessageChart(parseInt(rangeSelect.value || 7));
        } catch (error) {
            showToast('加载统计数据失败', 'error');
        }
    }

    async function loadBotSettings() {
        try {
            const settings = await apiFetch('/api/settings');

            document.getElementById('core_bot_token').value = settings.bot_token;
            document.getElementById('core_admin_id').value = settings.admin_id;
            document.getElementById('core_web_user').value = settings.web_user;

            document.getElementById('verification_enabled').checked = settings.verification_enabled;
            document.getElementById('verification_type').value = settings.verification_type;
            document.getElementById('verification_difficulty').value = settings.verification_difficulty;

            document.getElementById('update_method_dashboard').value = settings.update_method;
            document.getElementById('webhook_domain_dashboard').value = settings.webhook_domain || '';
            document.getElementById('webhook_secret_dashboard').value = settings.webhook_secret || '';
            toggleWebhookDashboardFields();
        } catch (error) {
            showToast('加载机器人设置失败', 'error');
        }
    }

    async function saveBotSettings() {
        const settings = {
            verification_enabled: document.getElementById('verification_enabled').checked,
            verification_type: document.getElementById('verification_type').value,
            verification_difficulty: document.getElementById('verification_difficulty').value,
            update_method: document.getElementById('update_method_dashboard').value,
            webhook_domain: document.getElementById('webhook_domain_dashboard').value,
            webhook_secret: document.getElementById('webhook_secret_dashboard').value,
        };
        try {
            const response = await apiFetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            showToast(response.message || '设置已保存');
        } catch (error) {
            showToast(`保存设置失败: ${error.message}`, 'error');
        }
    }

    async function saveCoreSettings() {
        const newPassword = document.getElementById('core_web_pass').value;
        const confirmPassword = document.getElementById('core_web_pass_confirm').value;

        if (newPassword !== confirmPassword) {
            showToast('两次输入的新密码不匹配！', 'error');
            return;
        }

        const settings = {
            bot_token: document.getElementById('core_bot_token').value,
            admin_id: document.getElementById('core_admin_id').value,
            web_user: document.getElementById('core_web_user').value,
            web_pass: newPassword,
        };

        try {
            const response = await apiFetch('/api/core-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            showToast(response.message || '核心设置已保存');
            document.getElementById('core_web_pass').value = '';
            document.getElementById('core_web_pass_confirm').value = '';
        } catch (error) {
            showToast(`保存核心设置失败: ${error.message}`, 'error');
        }
    }

    function toggleWebhookDashboardFields() {
        const method = document.getElementById('update_method_dashboard').value;
        const container = document.getElementById('webhook-settings-dashboard');
        container.style.display = (method === 'webhook') ? 'block' : 'none';
    }
    document.getElementById('update_method_dashboard').addEventListener('change', toggleWebhookDashboardFields);


    async function loadStartMessages() {
        try {
            const messages = await apiFetch('/api/start_messages');
            document.getElementById('start_message_zh').value = messages.zh;
            document.getElementById('start_message_en').value = messages.en;
        } catch (error) {
            showToast('加载欢迎消息失败', 'error');
        }
    }

    async function saveStartMessages() {
        const messages = {
            zh: document.getElementById('start_message_zh').value,
            en: document.getElementById('start_message_en').value,
        };
        try {
            const response = await apiFetch('/api/start_messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(messages)
            });
            showToast(response.message || '欢迎消息已保存');
        } catch (error) {
            showToast('保存欢迎消息失败', 'error');
        }
    }

    const saveSettingsBtn = document.getElementById('save-settings-btn');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', saveBotSettings);
    }
    const saveCoreSettingsBtn = document.getElementById('save-core-settings-btn');
    if (saveCoreSettingsBtn) {
        saveCoreSettingsBtn.addEventListener('click', saveCoreSettings);
    }
    const saveStartMsgBtn = document.getElementById('save-start-message-btn');
    if (saveStartMsgBtn) {
        saveStartMsgBtn.addEventListener('click', saveStartMessages);
    }


    const kwTbody = document.getElementById('keyword-list-tbody');
    const kwSearch = document.getElementById('keyword-search');
    const kwFilter = document.getElementById('keyword-filter');
    const kwPagination = document.getElementById('keyword-pagination');
    const kwInput = document.getElementById('keyword-input');
    const addKwBtn = document.getElementById('add-keyword-btn');

    function updateKwAndLoad(page = 1) {
        state.keywords.currentPage = page;
        loadKeywords();
    }

    function renderKeywords(data) {
        kwTbody.innerHTML = '';
        if (data.keywords.length === 0) {
            kwTbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary-color);">未找到关键词</td></tr>';
            return;
        }
        data.keywords.forEach(kw => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${escapeHTML(kw.keyword)}</strong></td>
                <td>${formatTime(kw.added_at)}</td>
                <td><button class="btn btn-danger btn-sm" data-id="${kw.id}">删除</button></td>
            `;
            tr.querySelector('button').addEventListener('click', () => deleteKeyword(kw.id, kw.keyword));
            kwTbody.appendChild(tr);
        });
        renderPagination(data.page, data.total_pages, kwPagination, updateKwAndLoad);
    }

    async function loadKeywords() {
        const { currentPage, search } = state.keywords;
        const url = `/api/keywords?page=${currentPage}&search=${encodeURIComponent(search)}`;
        try {
            const data = await apiFetch(url);
            state.keywords.list = data.keywords;
            renderKeywords(data);
        } catch (error) {
            showToast('加载关键词失败', 'error');
        }
    }

    async function addKeyword() {
        const inputValue = kwInput.value.trim();
        if (!inputValue) {
            showToast('请输入关键词', 'error');
            return;
        }
        const keywords = inputValue.split('\n').map(k => k.trim()).filter(k => k);
        try {
            const { added, exists } = await apiFetch('/api/keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords })
            });
            updateKwAndLoad(1);
            kwInput.value = '';
            showToast(`成功添加 ${added.length} 个关键词，已存在 ${exists.length} 个`);
        } catch (error) {
            showToast('添加关键词失败', 'error');
        }
    }

    async function deleteKeyword(id, keyword) {
        const confirmed = await customConfirm(
            '删除关键词',
            `确定要删除关键词 "${keyword}" 吗？`,
            '删除',
            'btn-danger'
        );
        if (!confirmed) return;
        try {
            await apiFetch(`/api/keywords/${id}`, { method: 'DELETE' });
            updateKwAndLoad();
            showToast('关键词删除成功');
        } catch (error) {
            showToast('删除关键词失败', 'error');
        }
    }

    addKwBtn.addEventListener('click', addKeyword);
    kwInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            addKeyword();
        }
    });

    kwSearch.addEventListener('input', debounce(() => {
        state.keywords.search = kwSearch.value.trim();
        updateKwAndLoad(1);
    }, 300));

    kwFilter.addEventListener('change', () => {
        state.keywords.filter = kwFilter.value;
        updateKwAndLoad(1);
    });

    const userTbody = document.getElementById('user-list-tbody');
    const userSearch = document.getElementById('user-search');
    const userFilter = document.getElementById('user-filter');
    const userPagination = document.getElementById('user-pagination');

    function renderPagination(currentPage, totalPages, container, loadFunc) {
        container.innerHTML = '';
        if (totalPages <= 1) return;
        const createBtn = (page, text = page, active = false, disabled = false) => {
            const btn = document.createElement('button');
            btn.textContent = text;
            if (page) btn.dataset.page = page;
            if (active) btn.classList.add('active');
            if (disabled) btn.disabled = true;
            if (page) btn.addEventListener('click', () => {
                loadFunc(page);
            });
            return btn;
        };
        container.appendChild(createBtn(currentPage > 1 ? currentPage - 1 : null, '«', false, currentPage === 1));
        let start = Math.max(1, currentPage - 2);
        let end = Math.min(totalPages, currentPage + 2);
        if (start > 1) container.appendChild(createBtn(1));
        if (start > 2) container.appendChild(createBtn(null, '...', false, true));
        for (let i = start; i <= end; i++) {
            container.appendChild(createBtn(i, i, i === currentPage));
        }
        if (end < totalPages - 1) container.appendChild(createBtn(null, '...', false, true));
        if (end < totalPages) container.appendChild(createBtn(totalPages));
        container.appendChild(createBtn(currentPage < totalPages ? currentPage + 1 : null, '»', false, currentPage === totalPages));
    }

    function updateUsersAndLoad(page = 1) {
        state.users.currentPage = page;
        loadUsers();
    }

    function renderUsers(data) {
        userTbody.innerHTML = '';
        if (data.users.length === 0) {
            userTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary-color);">未找到用户</td></tr>';
            return;
        }
        data.users.forEach(user => {
            const tr = document.createElement('tr');
            const username = user.username ? `@${user.username}` : (user.first_name || 'N/A');
            const statusBadge = user.is_blocked
                ? `<span class="badge badge-blocked">已屏蔽</span>`
                : `<span class="badge badge-active">正常</span>`;
            const verifyBadge = user.is_verified
                ? `<span class="badge badge-active">已验证</span>`
                : `<span class="badge" style="background: color-mix(in srgb, #fbbf24, transparent 90%); color: #fbbf24;">未验证</span>`;
            const actionButton = user.is_blocked
                ? `<button class="btn btn-success btn-sm" data-id="${user.id}">解禁</button>`
                : `<button class="btn btn-danger btn-sm" data-id="${user.id}">屏蔽</button>`;
            const verifyButton = user.is_verified
                ? `<button class="btn btn-sm" style="background: #f59e0b; color: white;" data-id="${user.id}">取消验证</button>`
                : `<button class="btn btn-success btn-sm" data-id="${user.id}">通过验证</button>`;
            tr.innerHTML = `
                <td>
                    <div class="user-info">
                        <strong>${escapeHTML(username)}</strong>
                        <span>${escapeHTML(user.first_name || '')} ${escapeHTML(user.last_name || '')}</span>
                    </div>
                </td>
                <td><code>${user.id}</code></td>
                <td>${statusBadge}</td>
                <td>${verifyBadge}</td>
                <td>${formatTime(user.last_seen)}</td>
                <td>
                    <div class="user-actions">
                        <button class="btn btn-sm btn-primary view-chat-btn" data-id="${user.id}">查看聊天</button>
                        ${actionButton}
                        ${verifyButton}
                    </div>
                </td>
            `;
            tr.querySelector('.view-chat-btn').addEventListener('click', () => {
                openChatModal(user.id);
            });

            const blockBtn = tr.querySelector('.btn-danger, .btn-success');
            blockBtn.addEventListener('click', () => {
                toggleUserBlock(user.id, !user.is_blocked);
            });

            const verifyBtn = tr.querySelectorAll('.btn-sm')[2];
            verifyBtn.addEventListener('click', () => {
                toggleUserVerify(user.id, !user.is_verified);
            });

            userTbody.appendChild(tr);
        });
        renderPagination(data.page, data.total_pages, userPagination, updateUsersAndLoad);
    }

    async function toggleUserVerify(userId, shouldVerify) {
        const action = shouldVerify ? 'verify' : 'unverify';
        const title = shouldVerify ? '通过验证' : '取消验证';
        const confirmMsg = shouldVerify ? '确定要通过此用户的验证吗？' : '确定要取消此用户的验证吗？';
        const confirmStyle = shouldVerify ? 'btn-success' : 'btn-danger';
        const confirmText = shouldVerify ? '通过' : '确认取消';
        const confirmed = await customConfirm(title, confirmMsg, confirmText, confirmStyle);
        if (!confirmed) return;
        try {
            await apiFetch(`/api/users/${userId}/${action}`, { method: 'POST' });
            showToast(shouldVerify ? '用户已通过验证' : '用户验证已取消');
            updateUsersAndLoad();
        } catch (error) {
            showToast('操作失败', 'error');
        }
    }

    async function loadUsers() {
        const { currentPage, search, filter } = state.users;
        const url = `/api/users?page=${currentPage}&search=${encodeURIComponent(search)}&filter=${filter}`;
        try {
            const data = await apiFetch(url);
            renderUsers(data);
        } catch (error) {
            showToast('加载用户列表失败', 'error');
        }
    }

    async function toggleUserBlock(userId, shouldBlock) {
        const action = shouldBlock ? 'block' : 'unblock';
        const title = shouldBlock ? '屏蔽用户' : '解禁用户';
        const confirmMsg = shouldBlock ? '确定要屏蔽此用户吗？' : '确定要解禁此用户吗？';
        const confirmStyle = shouldBlock ? 'btn-danger' : 'btn-success';
        const confirmText = shouldBlock ? '屏蔽' : '解禁';
        const confirmed = await customConfirm(title, confirmMsg, confirmText, confirmStyle);
        if (!confirmed) return;
        try {
            await apiFetch(`/api/users/${userId}/${action}`, { method: 'POST' });
            showToast(shouldBlock ? '用户已屏蔽' : '用户已解禁');
            updateUsersAndLoad();
        } catch (error) {
            showToast('操作失败', 'error');
        }
    }

    userSearch.addEventListener('input', debounce(() => {
        state.users.search = userSearch.value.trim();
        updateUsersAndLoad(1);
    }, 300));

    userFilter.addEventListener('change', () => {
        state.users.filter = userFilter.value;
        updateUsersAndLoad(1);
    });

    function escapeHTML(str) {
        return String(str || '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }

    function formatTime(isoString) {
        if (!isoString) return 'N/A';
        try {
            const date = new Date(isoString);

            const options = {
                timeZone: 'Asia/Shanghai',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                numberingSystem: 'latn'
            };

            const parts = new Intl.DateTimeFormat('en-US', options).formatToParts(date);
            const partMap = parts.reduce((acc, part) => {
                acc[part.type] = part.value;
                return acc;
            }, {});

            const ymd = `${partMap.year}/${partMap.month}/${partMap.day}`;
            const hms = `${partMap.hour}:${partMap.minute}:${partMap.second}`;

            const ms = String(date.getMilliseconds()).padStart(3, '0');

            return `${ymd} ${hms}.${ms}`;

        } catch (e) {
            try {
                const date = new Date(isoString);
                const oldFormatted = date.toLocaleString('sv-SE', { timeZone: 'Asia/Shanghai' });
                return oldFormatted.replace(/-/g, '/');
            } catch (e2) {
                 return isoString;
            }
        }
    }

    function debounce(func, delay) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    const chartCanvas = document.getElementById('messagesChart');
    function createOrUpdateChart(labels, data) {
        if (state.chart) {
            state.chart.data.labels = labels;
            state.chart.data.datasets[0].data = data;
            state.chart.update();
            return;
        }
        const ctx = chartCanvas.getContext('2d');
        state.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '消息数',
                    data: data,
                    fill: true,
                    tension: 0.2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    x: { display: true },
                    y: { display: true, beginAtZero: true }
                }
            }
        });
    }

    async function loadMessageChart(rangeDays = 7) {
        try {
            const data = await apiFetch(`/api/message_stats?range=${rangeDays}`);
            const labels = data.data.map(d => d.date);
            const counts = data.data.map(d => d.count);
            createOrUpdateChart(labels, counts);
        } catch (e) {
            showToast('加载消息统计失败', 'error');
        }
    }

    const rangeSelect = document.getElementById('range-select');
    rangeSelect.addEventListener('change', () => {
        loadMessageChart(parseInt(rangeSelect.value));
    });

    function openChatModal(userId) {
        state.chat.userId = userId;
        state.chat.page = 1;
        loadChatMessages();
        const modal = document.getElementById('chat-modal');
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);
    }

    async function loadChatMessages() {
        const s = state.chat;
        const url = `/api/user_messages?user_id=${s.userId}&page=${s.page}&search=${encodeURIComponent(s.search)}&start=${s.start}&end=${s.end}`;
        try {
            const data = await apiFetch(url);

            const list = document.getElementById('chat-list');
            list.innerHTML = '';

            if (data.messages.length === 0) {
                list.innerHTML = `<p style="color:var(--text-secondary-color);text-align:center;">无聊天记录</p>`;
            } else {
                data.messages.forEach(m => {
                    const div = document.createElement('div');
                    div.style.padding = '0.5rem 0';
                    div.innerHTML = `
                        <div style="font-size:0.85rem;color:var(--text-secondary-color);">${formatTime(m.sent_at)}</div>
                        <div>${escapeHTML(m.text || '')}</div>
                        <hr>
                    `;
                    list.appendChild(div);
                });
            }

            renderPagination(data.page, data.total_pages, document.getElementById('chat-pagination'), (p) => {
                state.chat.page = p;
                loadChatMessages();
            });

        } catch(e) {
            showToast('加载聊天记录失败', 'error');
        }
    }

    document.getElementById('chat-search').addEventListener('input', debounce(() => {
        state.chat.search = document.getElementById('chat-search').value.trim();
        state.chat.page = 1;
        loadChatMessages();
    }, 300));

    document.getElementById('chat-start').addEventListener('change', () => {
        state.chat.start = document.getElementById('chat-start').value;
        state.chat.page = 1;
        loadChatMessages();
    });

    document.getElementById('chat-end').addEventListener('change', () => {
        state.chat.end = document.getElementById('chat-end').value;
        state.chat.page = 1;
        loadChatMessages();
    });

    document.getElementById('chat-close').addEventListener('click', () => {
        const modal = document.getElementById('chat-modal');
        modal.classList.remove('show');
        setTimeout(() => modal.style.display = 'none', 300);
    });

    switchPage('dashboard');
});