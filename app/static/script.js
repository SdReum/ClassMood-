async function upload() {
    const files = document.getElementById('fileInput').files;
    const formData = new FormData();
    for (let f of files) formData.append('files', f);

    const token = localStorage.getItem('token');
    if (!token) {
        alert('Set token in localStorage: localStorage.setItem("token", "your_token")');
        return;
    }

    const res = await fetch('/media/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    const data = await res.json();
    const resultsEl = document.getElementById('results');
    if (res.ok) {
        resultsEl.innerHTML = '<p style="color: green;">Uploaded: ' +
            data.results.map(r => r.filename).join(', ') + '</p>';
        // Refresh the file list after successful upload
        loadUserFiles();
    } else {
        resultsEl.innerHTML = '<p style="color: red;">Error: ' + (data.detail || 'Unknown') + '</p>';
    }
}

async function loadUserFiles() {
    const token = localStorage.getItem('token');
    const res = await fetch('/media/files', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    const filesEl = document.getElementById('user-files');
    if (res.ok) {
        filesEl.innerHTML = data.files.map(f => `
            <div style="margin: 0.5rem 0; padding: 0.5rem; border: 1px solid #ccc;">
                <span>${f.filename} (${new Date(f.uploaded_at).toLocaleString()})</span>
                <button onclick="deleteFile(${f.id})" style="margin-left: 1rem;">Delete</button>
            </div>
        `).join('');
    } else {
        filesEl.innerHTML = '<p style="color: red;">Error loading files</p>';
    }
}

async function deleteFile(id) {
    if (!confirm("Delete this file?")) return;
    const token = localStorage.getItem('token');
    const res = await fetch(`/media/files/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        loadUserFiles(); // обнови список
    } else {
        alert('Delete failed');
    }
}

// Проверка токена при загрузке страницы с валидацией на сервере и редиректами между /auth и /upload
async function checkAuth() {
    // 1) Определяем перезапуск сервера и при необходимости выходим из аккаунта
    try {
        const bootRes = await fetch('/meta/boot');
        if (bootRes.ok) {
            const { boot_id } = await bootRes.json();
            const prevBoot = localStorage.getItem('boot_id');
            if (prevBoot && prevBoot !== boot_id) {
                // Сервер перезапустился — сбрасываем токен
                localStorage.removeItem('token');
            }
            localStorage.setItem('boot_id', boot_id);
        }
    } catch (e) {
        // Если не удалось получить boot_id — ничего не меняем
    }

    const token = localStorage.getItem('token');
    let path = window.location.pathname || '/';
    if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
    const onAuthPage = path === '/' || path === '/auth' || path.startsWith('/auth?');
    const onUploadPage = path === '/upload' || path.startsWith('/upload?');
    const onProfilePage = path === '/profile' || path.startsWith('/profile?');
    const onAlgorithmPage = path === '/algorithm' || path.startsWith('/algorithm?');

    if (!token) {
        if (onUploadPage || onProfilePage || onAlgorithmPage) {
            // Нет токена на странице загрузки — уходим на авторизацию
            window.location.replace('/auth');
            return;
        }
        // На auth-странице просто показать формы (если есть)
        const tabs = document.querySelector('.tabs');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        if (tabs && loginForm && registerForm) {
            tabs.classList.remove('hidden');
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
        }
        return;
    }
    try {
        const res = await fetch('/media/files', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            // Токен валиден
            if (onAuthPage) {
                // Если на auth, переходим к загрузке
                window.location.replace('/upload');
                return;
            }
            if (onUploadPage || onProfilePage || onAlgorithmPage) {
                // Уже на странице загрузки — подгрузим файлы, если есть UI
                if (typeof loadUserFiles === 'function') {
                    loadUserFiles();
                }
                // Обновим отображение имени, если есть такой элемент
                try {
                    const me = await getCurrentUser();
                    const nameEl = document.getElementById('profile-username');
                    if (nameEl && me && me.username) nameEl.textContent = me.username;
                } catch {}
            }
        } else {
            // Токен невалиден
            localStorage.removeItem('token');
            if (onUploadPage || onProfilePage || onAlgorithmPage) {
                window.location.replace('/auth');
                return;
            }
            // На auth-странице — показываем формы, если есть
            const tabs = document.querySelector('.tabs');
            const loginForm = document.getElementById('login-form');
            const registerForm = document.getElementById('register-form');
            if (tabs && loginForm && registerForm) {
                tabs.classList.remove('hidden');
                loginForm.classList.remove('hidden');
                registerForm.classList.add('hidden');
            }
        }
    } catch (e) {
        localStorage.removeItem('token');
        if (onUploadPage) {
            window.location.replace('/auth');
            return;
        }
        const tabs = document.querySelector('.tabs');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        if (tabs && loginForm && registerForm) {
            tabs.classList.remove('hidden');
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
        }
    }
}

// Глобальный logout — очищает токен и уводит на /auth
function logout() {
    localStorage.removeItem('token');
    window.location.replace('/auth');
}

// Получение текущего пользователя
async function getCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    const res = await fetch('/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return null;
    return await res.json();
}

// Helper to show username in nav if element exists
async function showUsernameInNav() {
    try {
        const me = await getCurrentUser();
        const nameEl = document.getElementById('profile-username');
        if (nameEl && me && me.username) nameEl.textContent = me.username;
    } catch (e) {
        console.error('Failed to show username in nav:', e);
    }
}