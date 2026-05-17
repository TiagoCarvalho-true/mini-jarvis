// Websocket para eventos em tempo real
const ws = new WebSocket(`ws://${location.host}/ws/events`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'log') {
        addLog(data.message);
    } else if (data.type === 'chat') {
        addMessage(data.role, data.content);
    } else if (data.type === 'status_update') {
        updateStatus(data.status);
    }
};

function addLog(msg) {
    const container = document.getElementById('log-container');
    const div = document.createElement('div');
    div.className = 'log-entry';
    const time = new Date().toLocaleTimeString();
    div.innerHTML = `<span class="time">[${time}]</span> ${msg}`;
    container.prepend(div);
}

function addMessage(role, content) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `message ${role === 'user' ? 'user-msg' : 'jarvis-msg'}`;
    div.innerText = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function updateStatus(status) {
    document.getElementById('uptime').innerText = status.uptime;
}

async function loadInitialData() {
    // Carrega historico
    const histResp = await fetch('/history');
    const history = await histResp.json();
    history.forEach(m => addMessage(m.role, m.content));

    // Carrega dispositivos
    const devResp = await fetch('/api/devices');
    const devices = await devResp.json();
    renderDevices(devices);

    // Carrega rostos
    const faceResp = await fetch('/api/faces');
    const faces = await faceResp.json();
    renderFaces(faces);
    
    // Atualiza status a cada 5s
    setInterval(async () => {
        const sResp = await fetch('/api/status');
        const status = await sResp.json();
        updateStatus(status);
    }, 5000);
}

function renderDevices(devices) {
    const container = document.getElementById('iot-container');
    container.innerHTML = '';
    devices.forEach(d => {
        const div = document.createElement('div');
        div.className = 'node-card';
        div.innerHTML = `
            <div class="name">${d.name}</div>
            <div class="label">${d.id}</div>
            <button class="btn" onclick="sendCommand('${d.id}', 'on')">ON</button>
            <button class="btn" onclick="sendCommand('${d.id}', 'off')">OFF</button>
        `;
        container.appendChild(div);
    });
}

function renderFaces(faces) {
    const container = document.getElementById('face-container');
    container.innerHTML = '';
    faces.forEach(name => {
        const div = document.createElement('div');
        div.className = 'node-card';
        div.innerHTML = `
            <div class="avatar">👤</div>
            <div class="name">${name}</div>
            <button class="btn" style="background:var(--secondary)" onclick="deleteFace('${name}')">DEL</button>
        `;
        container.appendChild(div);
    });
}

async function sendCommand(id, action) {
    addLog(`Enviando comando ${action} para ${id}...`);
    await fetch(`/api/devices/${id}/command?action=${action}`, { method: 'POST' });
}

// Upload de Rosto
document.getElementById('face-upload').onchange = async (e) => {
    const file = e.target.files[0];
    const name = document.getElementById('face-name').value;
    if (!name || !file) return alert("Preencha o nome e selecione a foto!");

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);

    addLog(`Cadastrando rosto: ${name}...`);
    const resp = await fetch('/api/faces/register', {
        method: 'POST',
        body: formData
    });
    
    if (resp.ok) {
        addLog(`Rosto ${name} cadastrado!`);
        location.reload();
    }
};

async function deleteFace(name) {
    if (!confirm(`Excluir rosto de ${name}?`)) return;
    await fetch(`/api/faces/${name}`, { method: 'DELETE' });
    location.reload();
}

loadInitialData();
