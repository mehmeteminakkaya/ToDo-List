document.addEventListener('DOMContentLoaded', function() {
    // === Notification System (Toasts) ===
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;
        
        const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');
        toast.innerHTML = `<span class="toast-icon">${icon}</span> ${message}`;
        
        container.appendChild(toast);

        // Remove toast after 4 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    }

    // === Add Todo JS ===
    const todoForm = document.getElementById('todoForm');
    if (todoForm) {
        todoForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const form = event.target;
            const addBtn = document.getElementById('addBtn');
            const originalBtnText = addBtn.innerHTML;

            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            const payload = {
                title: data.title,
                description: data.description || "AI tarafından oluşturulacak...",
                priority: parseInt(data.priority) || 3,
                completed: false
            };

            try {
                // UI Feedback: Loading
                addBtn.disabled = true;
                addBtn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span> AI Planlıyor...';
                
                const response = await fetch('/todo/todo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getCookie('access_token')}`
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    showToast('Görev başarıyla eklendi! ✨', 'success');
                    setTimeout(() => window.location.href = '/todo/todo-page', 1000);
                } else {
                    const errorData = await response.json();
                    showToast(`Hata: ${errorData.detail}`, 'error');
                }
            } catch (error) {
                showToast('Bir hata oluştu. Lütfen tekrar dene.', 'error');
            } finally {
                addBtn.disabled = false;
                addBtn.innerHTML = originalBtnText;
            }
        });
    }

    // === Edit/Delete Todo JS ===
    const editTodoForm = document.getElementById('editTodoForm');
    if (editTodoForm) {
        editTodoForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            const urlParts = window.location.pathname.split('/');
            const todoId = urlParts[urlParts.length - 1];

            const payload = {
                title: data.title,
                description: data.description,
                priority: parseInt(data.priority),
                completed: data.completed === "on" || form.querySelector('.toggle-input')?.checked
            };

            try {
                const response = await fetch(`/todo/todo/${todoId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getCookie('access_token')}`
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    showToast('Güncellendi! 👍', 'success');
                    setTimeout(() => window.location.href = '/todo/todo-page', 800);
                } else {
                    showToast('Güncelleme başarısız oldu.', 'error');
                }
            } catch (error) {
                showToast('Hata oluştu.', 'error');
            }
        });

        const deleteBtn = document.getElementById('deleteButton');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async function () {
                if (!confirm('Bu görevi silmek istediğine emin misin?')) return;
                
                const urlParts = window.location.pathname.split('/');
                const todoId = urlParts[urlParts.length - 1];

                try {
                    const response = await fetch(`/todo/todo/${todoId}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
                    });

                    if (response.ok) {
                        showToast('Görev silindi.', 'info');
                        setTimeout(() => window.location.href = '/todo/todo-page', 800);
                    }
                } catch (error) {
                    showToast('Silme işlemi başarısız.', 'error');
                }
            });
        }
    }

    // === Login JS ===
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const payload = new URLSearchParams(formData);

            try {
                const response = await fetch('/auth/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: payload.toString()
                });

                if (response.ok) {
                    const data = await response.json();
                    document.cookie = `access_token=${data.access_token}; path=/; max-age=86400`;
                    showToast('Başarıyla giriş yapıldı! 🚀', 'success');
                    setTimeout(() => window.location.href = '/todo/todo-page', 1000);
                } else {
                    showToast('Giriş başarısız. Bilgilerini kontrol et.', 'error');
                }
            } catch (error) {
                showToast('Bir ağ hatası oluştu.', 'error');
            }
        });
    }

    // === Register JS ===
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());

            if (data.password !== data.password2) {
                showToast('Şifreler eşleşmiyor!', 'error');
                return;
            }

            const payload = {
                email: data.email,
                username: data.username,
                first_name: data.firstname,
                last_name: data.lastname,
                role: data.role,
                phone_number: data.phone_number,
                password: data.password
            };

            try {
                const response = await fetch('/auth/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    showToast('Hesabın başarıyla oluşturuldu! 🎉', 'success');
                    setTimeout(() => window.location.href = '/auth/login-page', 1500);
                } else {
                    const error = await response.json();
                    showToast(`Hata: ${error.detail}`, 'error');
                }
            } catch (error) {
                showToast('Kayıt sırasında hata oluştu.', 'error');
            }
        });
    }
});

// === Global Helper Functions ===
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function logout() {
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    window.location.href = '/auth/login-page';
}

// Dashboard Quick Toggle
async function toggleTodo(id) {
    try {
        const response = await fetch(`/todo/todo/${id}/toggle`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${getCookie('access_token')}` }
        });
        if (response.ok) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Toggle error:', error);
    }
}

// === AI Assistant Sidebar Logic ===
function toggleAISidebar() {
    const sidebar = document.getElementById('ai-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

// Global scope access for HTML onclicks
window.toggleAISidebar = toggleAISidebar;
window.toggleTodo = toggleTodo;
window.logout = logout;

// AI Chat Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const aiChatForm = document.getElementById('aiChatForm');
    const aiChatInput = document.getElementById('aiChatInput');
    const aiChatMessages = document.getElementById('ai-chat-messages');

    if (aiChatForm) {
        aiChatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const message = aiChatInput.value.trim();
            if (!message) return;

            // 1. Add User Message
            appendChatBubble(message, 'user');
            aiChatInput.value = '';

            // 2. Add AI Loading State
            const loadingBubble = appendChatBubble('Gemini düşünüyor...', 'ai');

            try {
                const response = await fetch('/todo/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getCookie('access_token')}`
                    },
                    body: JSON.stringify({ message: message })
                });

                if (response.ok) {
                    const data = await response.json();
                    loadingBubble.innerHTML = data.response;
                } else {
                    loadingBubble.innerHTML = 'Bir hata oluştu. Lütfen tekrar dene.';
                    loadingBubble.classList.add('toast-error');
                }
            } catch (error) {
                loadingBubble.innerHTML = 'Ağ bağlantısı kurulamadı.';
            } finally {
                // Scroll to bottom
                aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
            }
        });
    }

    function appendChatBubble(text, sender) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;
        bubble.innerHTML = text;
        aiChatMessages.appendChild(bubble);
        aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
        return bubble;
    }
});