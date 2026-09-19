let currentSessionId = null;

const els = {
    chatLog: document.getElementById('chat-log'),
    userInput: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    restartBtn: document.getElementById('restart-btn'),
    stateDisplay: document.getElementById('state-display'),
    documentDisplay: document.getElementById('document-display'),
    errorBanner: document.getElementById('error-banner'),
    errorMessage: document.getElementById('error-message'),
    dismissError: document.getElementById('dismiss-error')
};

// Event Listeners
els.sendBtn.addEventListener('click', sendMessage);
els.userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
els.restartBtn.addEventListener('click', initSession);
els.dismissError.addEventListener('click', hideError);

async function initSession() {
    hideError();
    els.chatLog.innerHTML = '';
    els.stateDisplay.innerHTML = '';
    els.documentDisplay.innerHTML = '';
    
    try {
        const res = await fetch('/api/session', { method: 'POST' });
        if (!res.ok) throw new Error('Failed to start session');
        
        const data = await res.json();
        currentSessionId = data.session_id;
        
        appendMessage('bot', "Hello! I am your intake assistant. Let's start with your personal wishes document. What is your full name?");
        renderState(data.state);
        els.userInput.focus();
    } catch (err) {
        showError(err.message);
    }
}

async function sendMessage() {
    const text = els.userInput.value.trim();
    if (!text || !currentSessionId) return;
    
    // Disable inputs
    els.userInput.value = '';
    els.userInput.disabled = true;
    els.sendBtn.disabled = true;
    
    appendMessage('user', text);
    hideError();
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: text
            })
        });
        
        if (!res.ok) throw new Error('Network error. Please try again.');
        
        const data = await res.json();
        appendMessage('bot', data.assistant_message);
        renderState(data.state);
        els.documentDisplay.innerHTML = marked.parse(data.document);
    } catch (err) {
        showError("Something went wrong — please try again.");
    } finally {
        els.userInput.disabled = false;
        els.sendBtn.disabled = false;
        els.userInput.focus();
    }
}

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = text;
    els.chatLog.appendChild(div);
    els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderState(state) {
    els.stateDisplay.innerHTML = '';
    
    const fields = [
        { key: 'full_name', label: 'Full Name' },
        { key: 'home_address', label: 'Home Address' },
        { key: 'covers_worldwide_assets', label: 'Covers Worldwide Assets' },
        { key: 'has_children', label: 'Has Children' },
        { key: 'children_names', label: 'Children Names' },
        { key: 'executor.name', label: 'Executor Name', nested: 'executor', subKey: 'name' },
        { key: 'executor.relationship', label: 'Executor Relationship', nested: 'executor', subKey: 'relationship' },
        { key: 'specific_gifts', label: 'Specific Gifts' },
        { key: 'additional_wishes', label: 'Additional Wishes' }
    ];
    
    fields.forEach(f => {
        let val;
        if (f.nested) {
            val = state[f.nested] ? state[f.nested][f.subKey] : null;
        } else {
            val = state[f.key];
        }
        
        const row = document.createElement('div');
        row.className = 'state-row';
        
        const keyEl = document.createElement('div');
        keyEl.className = 'state-key';
        keyEl.textContent = f.label;
        
        const valEl = document.createElement('div');
        valEl.className = 'state-val';
        
        if (val === null || val === undefined || (Array.isArray(val) && val.length === 0)) {
            valEl.textContent = 'Not yet provided';
            valEl.classList.add('muted');
        } else if (Array.isArray(val)) {
            valEl.textContent = val.join(', ');
        } else if (typeof val === 'boolean') {
            valEl.textContent = val ? 'Yes' : 'No';
        } else {
            valEl.textContent = val;
        }
        
        row.appendChild(keyEl);
        row.appendChild(valEl);
        els.stateDisplay.appendChild(row);
    });
}

function showError(msg) {
    els.errorMessage.textContent = msg;
    els.errorBanner.classList.remove('hidden');
}

function hideError() {
    els.errorBanner.classList.add('hidden');
}

// Start
initSession();
