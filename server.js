import express from 'express';
import session from 'express-session';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(session({
  secret: 'bot-suite-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 86400000 }
}));

let botProcess = null;
let taskState = {
  status: 'Idle',
  email: '',
  logs: ['System initialized. Web Console connected to bot.py engine.']
};

function addLog(msg) {
  const timestamp = new Date().toLocaleTimeString();
  const cleanMsg = msg.toString().trim();
  if (cleanMsg) {
    taskState.logs.unshift(`[${timestamp}] ${cleanMsg}`);
    if (taskState.logs.length > 100) taskState.logs.pop();
  }
}

// 1. Dashboard Web UI
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Bot Suite Web Console</title>
      <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #f8fafc; margin: 0; padding: 30px 20px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 750px; background: #1e293b; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
        h1 { margin-top: 0; color: #38bdf8; font-size: 24px; text-align: center; }
        .badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; background: #334155; color: #38bdf8; }
        .status-box { margin: 20px 0; padding: 15px; background: #0f172a; border-radius: 8px; border-left: 4px solid #38bdf8; display: flex; justify-content: space-between; align-items: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-size: 14px; font-weight: 500; color: #94a3b8; }
        input[type="text"], input[type="email"] { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 15px; }
        input:focus { outline: none; border-color: #38bdf8; }
        button { width: 100%; padding: 12px; border-radius: 6px; border: none; background: #0284c7; color: white; font-weight: 600; font-size: 15px; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; }
        .logs-title { margin-top: 30px; margin-bottom: 10px; font-size: 16px; color: #94a3b8; display: flex; justify-content: space-between; }
        .log-box { background: #090d16; border: 1px solid #334155; border-radius: 8px; padding: 15px; height: 260px; overflow-y: auto; font-family: monospace; font-size: 13px; color: #a7f3d0; }
        .log-entry { margin-bottom: 6px; border-bottom: 1px solid #1e293b; padding-bottom: 4px; }
        .flex-row { display: flex; gap: 10px; }
      </style>
      <script>
        // Auto-refresh console output every 4 seconds
        setTimeout(() => { window.location.reload(); }, 4000);
      </script>
    </head>
    <body>
      <div class="container">
        <h1>⚙️ Bot Suite Web Console</h1>
        
        <div class="status-box">
          <div>Status: <span class="badge">${taskState.status}</span></div>
          ${botProcess ? '<span style="color: #4ade80; font-size: 12px;">● Engine Active</span>' : '<span style="color: #94a3b8; font-size: 12px;">○ Idle</span>'}
        </div>

        <!-- Start Task Form -->
        <form action="/api/start" method="POST" class="form-group">
          <label>Target Email Address:</label>
          <div class="flex-row">
            <input type="email" name="email" placeholder="user@joblymail.in" value="${taskState.email}" required />
            <button type="submit" style="width: 150px;">Run bot.py</button>
          </div>
        </form>

        <!-- Submit OTP Form -->
        <form action="/api/submit-otp" method="POST" class="form-group">
          <label>Verification OTP Code:</label>
          <div class="flex-row">
            <input type="text" name="otp" placeholder="Enter 6-digit OTP code" required />
            <button type="submit" style="width: 150px; background: #16a34a;">Send OTP</button>
          </div>
        </form>

        <div class="logs-title">
          <span>Live Output Stream (bot.py)</span>
          <a href="/" style="color: #38bdf8; text-decoration: none; font-size: 13px;">Refresh Console</a>
        </div>
        <div class="log-box">
          ${taskState.logs.map(log => `<div class="log-entry">${log}</div>`).join('')}
        </div>
      </div>
    </body>
    </html>
  `);
});

// 2. Start Task API Endpoint (Triggers python3 -u bot.py)
app.post('/api/start', (req, res) => {
  const { email } = req.body;
  taskState.email = email;
  
  if (botProcess) {
    addLog('⚠️ Stopping active previous bot process...');
    try { botProcess.kill(); } catch (e) {}
  }

  addLog(`🚀 Launching bot.py engine for email: ${email}`);
  taskState.status = 'Running (Awaiting OTP)';

  const botPath = path.join(__dirname, 'bot.py');
  botProcess = spawn('python3', ['-u', botPath], { cwd: __dirname });

  // Automatically pass email to bot.py stdin
  setTimeout(() => {
    if (botProcess && botProcess.stdin) {
      botProcess.stdin.write(`${email}\n`);
      addLog(`📧 Sent email '${email}' to bot.py stdin prompt.`);
    }
  }, 1000);

  // Capture stdout output
  botProcess.stdout.on('data', (data) => {
    addLog(data.toString());
  });

  // Capture stderr output
  botProcess.stderr.on('data', (data) => {
    addLog(`[STDERR] ${data.toString()}`);
  });

  botProcess.on('close', (code) => {
    addLog(`🏁 bot.py finished execution with exit code ${code}`);
    taskState.status = `Completed (Exit Code ${code})`;
    botProcess = null;
  });

  res.redirect('/');
});

// 3. Submit OTP API Endpoint (Sends OTP to bot.py stdin)
app.post('/api/submit-otp', (req, res) => {
  const { otp } = req.body;
  taskState.otp = otp;
  
  if (botProcess && botProcess.stdin) {
    botProcess.stdin.write(`${otp}\n`);
    addLog(`🔑 Sent OTP Code '${otp}' to bot.py process.`);
    taskState.status = 'Processing OTP Code...';
  } else {
    addLog(`⚠️ No active bot.py process found to receive OTP.`);
  }

  res.redirect('/');
});

app.listen(PORT, () => {
  console.log(`🚀 Bot Suite Web Console connected and running at http://localhost:${PORT}`);
});
