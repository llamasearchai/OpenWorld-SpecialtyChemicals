const logEl = document.getElementById('log');
document.getElementById('connect').onclick = () => {
  const ws = new WebSocket(`ws://${location.host}/ws/effluent`);
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    const line = JSON.stringify(msg);
    logEl.textContent = (line + "\n" + logEl.textContent).slice(0, 4000);
  };
};


