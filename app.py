import streamlit as st
import streamlit.components.v1 as components

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from google import genai


def make_ai_handler(api_key):
    class AIHandler(BaseHTTPRequestHandler):
        def send_json(self, status_code, data):
            body = json.dumps(data).encode("utf-8")
            origin = self.headers.get("Origin", "")
            parsed = urlparse(origin)
            allowed_origin = (
                parsed.scheme == "http"
                and parsed.hostname in ("localhost", "127.0.0.1")
            )

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if allowed_origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_json(200, {"ok": True})

        def do_POST(self):
            if self.path != "/correct":
                self.send_json(404, {"error": "Endpoint not found"})
                return

            origin = self.headers.get("Origin", "")
            parsed = urlparse(origin)
            if not (
                parsed.scheme == "http"
                and parsed.hostname in ("localhost", "127.0.0.1")
            ):
                self.send_json(403, {"error": "Local app access only"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 100000:
                    self.send_json(413, {"error": "Text is too large"})
                    return

                data = json.loads(self.rfile.read(length))
                text = data.get("text", "")
                if not isinstance(text, str) or not text.strip():
                    self.send_json(400, {"error": "Please provide text"})
                    return
                if len(text) > 20000:
                    self.send_json(
                        413,
                        {"error": "Maximum 20,000 characters per request"},
                    )
                    return

                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=(
                        "You are a careful grammar and transcription editor. "
                        "Correct grammar, spelling, punctuation and capitalization. "
                        "Preserve the original meaning, names and intent. "
                        "Keep the original language; do not translate Hindi, "
                        "English or Hinglish into another language. "
                        "Do not add facts or explanations. "
                        "Return only the corrected transcript.\n\n"
                        "TRANSCRIPT:\n" + text
                    ),
                )
                corrected = response.text
                if not corrected or not corrected.strip():
                    self.send_json(
                        502, {"error": "Gemini returned an empty response"}
                    )
                    return
                self.send_json(200, {"corrected_text": corrected.strip()})
            except Exception as error:
                print("Gemini correction error:", repr(error))
                self.send_json(
                    502,
                    {
                        "error": (
                            "AI correction unavailable. Check API quota, "
                            "model availability or internet connection."
                        )
                    },
                )

        def log_message(self, format, *args):
            pass

    return AIHandler


@st.cache_resource
def start_ai_bridge(api_key):
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8765),
        make_ai_handler(api_key),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


st.set_page_config(
    page_title="AI Voice Typewriter",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Streamlit page-level styling (outside the embedded workspace).
st.markdown(
    """
    <style>
      :root { color-scheme: dark; }
      .stApp {
        background:
          radial-gradient(ellipse at 12% 0%, rgba(109, 40, 217, .16), transparent 36%),
          radial-gradient(ellipse at 95% 8%, rgba(37, 99, 235, .12), transparent 30%),
          #090b13;
        color: #eef0ff;
      }
      [data-testid="stHeader"] { background: transparent; }
      [data-testid="stToolbar"] { right: 1rem; }
      .block-container { max-width: 1240px; padding-top: 1.2rem; padding-bottom: 2rem; }
      [data-testid="stAlert"] { border-radius: 12px; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    GEMINI_API_KEY = ""

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    try:
        start_ai_bridge(GEMINI_API_KEY)
    except OSError:
        st.warning(
            "AI bridge could not start. Port 8765 may already be in use. "
            "Voice typing and other features can still work."
        )
else:
    st.warning(
        "Gemini API key not configured. AI correction is unavailable; "
        "basic correction and other features remain available."
    )

components.html(
    r"""
    <div id="studio">
      <style>
        :root {
          color-scheme: dark;
          --bg: #0b0d17;
          --panel: #121522;
          --panel2: #171a2a;
          --border: #292d43;
          --text: #f3f4ff;
          --muted: #a1a7c2;
          --purple: #8b5cf6;
          --purple2: #6d28d9;
          --blue: #4f7cff;
          --green: #22c55e;
          --red: #fb7185;
        }
        * { box-sizing: border-box; }
        #studio {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--text);
          background:
            radial-gradient(ellipse at 8% 0%, rgba(124,58,237,.15), transparent 34%),
            radial-gradient(ellipse at 98% 4%, rgba(59,130,246,.11), transparent 30%),
            var(--bg);
          padding: 22px;
          border: 1px solid #24283c;
          border-radius: 22px;
          min-height: 900px;
        }
        .topbar { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:24px; }
        .brand { display:flex; align-items:center; gap:14px; min-width:0; }
        .brand-icon {
          width:54px;height:54px;border-radius:17px;display:grid;place-items:center;
          background:linear-gradient(145deg,#9b72ff,#5b35c9);
          box-shadow:0 8px 30px rgba(124,58,237,.28);font-size:26px;
        }
        h1 { font-size:clamp(24px,4vw,34px); line-height:1.15; letter-spacing:-.8px; margin:0; font-weight:760; }
        .subtitle { color:var(--muted); margin-top:6px; font-size:13px; }
        .pill { border:1px solid #3b315f;background:#211a36;color:#d7c8ff;padding:8px 12px;border-radius:999px;font-size:12px;white-space:nowrap; }
        .section { background:linear-gradient(145deg,rgba(21,24,40,.96),rgba(16,18,30,.96)); border:1px solid var(--border); border-radius:18px; padding:18px; margin-bottom:16px; box-shadow:0 10px 32px rgba(0,0,0,.12); }
        .section-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:14px; }
        .section-title { font-size:15px; font-weight:700; display:flex; align-items:center; gap:9px; }
        .section-note { color:var(--muted);font-size:12px; }
        .top-grid { display:grid; grid-template-columns:1.3fr 1fr 1fr; gap:12px; margin-bottom:16px; }
        .metric { border:1px solid var(--border);background:#111421;border-radius:14px;padding:13px 15px;min-width:0; }
        .metric-label { color:var(--muted);font-size:11px;letter-spacing:.5px;text-transform:uppercase; }
        .metric-value { font-size:17px;font-weight:700;margin-top:5px;overflow-wrap:anywhere; }
        .status-dot { display:inline-block;width:8px;height:8px;border-radius:50%;background:#64748b;margin-right:7px;vertical-align:1px; }
        .status-dot.live { background:var(--green);box-shadow:0 0 0 5px rgba(34,197,94,.1);animation:pulse 1.5s infinite; }
        @keyframes pulse { 50% { box-shadow:0 0 0 8px rgba(34,197,94,0); } }
        .toolbar { display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px; }
        .language-wrap { display:flex;align-items:center;gap:10px;flex-wrap:wrap; }
        label { color:#c6cbe0;font-size:12px;font-weight:600; }
        select {
          background:#0e1120;color:var(--text);border:1px solid #353a55;border-radius:10px;
          padding:10px 12px;min-width:180px;font-size:13px;outline:none;
        }
        button {
          appearance:none;border:1px solid #353a55;background:#1b1f31;color:#f3f4ff;
          padding:10px 13px;border-radius:10px;font-weight:650;font-size:12px;
          cursor:pointer;transition:transform .15s,border-color .15s,filter .15s,background .15s;
        }
        button:hover { border-color:#8270c5;filter:brightness(1.09);transform:translateY(-1px); }
        button:active { transform:translateY(0); }
        button:disabled { opacity:.55;cursor:not-allowed;transform:none; }
        .primary { background:linear-gradient(135deg,#8b5cf6,#6d3bdb);border-color:#936df9;box-shadow:0 7px 20px rgba(109,40,217,.2); }
        .primary:hover { background:linear-gradient(135deg,#9a70ff,#7849e8); }
        .stop { background:#2a1724;border-color:#5d293e;color:#ffb8c7; }
        .success { background:linear-gradient(135deg,#16834d,#11683f);border-color:#259b60; }
        .ai-button { background:linear-gradient(135deg,#7042d6,#4931a5);border-color:#8865e9; }
        .editor-wrap { border:1px solid #333851;background:#0b0e19;border-radius:14px;padding:10px; }
        textarea {
          display:block;width:100%;resize:vertical;background:transparent;color:#eef0ff;border:0;outline:none;
          font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px;line-height:1.8;
          padding:10px;min-height:250px;
        }
        textarea::placeholder { color:#6f7693; }
        .editor-footer { display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;border-top:1px solid #22263a;padding:10px 8px 2px;color:var(--muted);font-size:11px; }
        .inline-actions { display:flex;gap:8px;flex-wrap:wrap; }
        .help { color:var(--muted);font-size:12px;line-height:1.6;margin:0 0 14px; }
        .correction-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px; }
        .tool-card { background:#0e1120;border:1px solid #2a2e45;border-radius:13px;padding:14px; }
        .tool-card h3 { font-size:13px;margin:0 0 6px;font-weight:700; }
        .tool-card p { color:var(--muted);font-size:11px;line-height:1.55;min-height:35px;margin:0 0 12px; }
        #correctedOutput { min-height:170px;border:1px solid #333851;border-radius:12px;background:#0b0e19;margin-top:12px;padding:14px; }
        .preview-label { display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:16px;margin-bottom:8px; }
        .preview-chip { color:#c7b6ff;background:#211936;border:1px solid #44316d;border-radius:999px;padding:5px 9px;font-size:10px; }
        .download-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px; }
        .download-card { display:flex;align-items:center;gap:12px;text-align:left;width:100%;padding:15px;background:#101321;border:1px solid #2d3249;border-radius:13px; }
        .file-icon { display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:#20203b;font-size:20px;flex-shrink:0; }
        .download-title { font-size:13px;font-weight:700; }
        .download-sub { color:var(--muted);font-size:11px;margin-top:4px;font-weight:400; }
        #statusMessage { margin-top:12px;padding:10px 12px;background:#111827;border:1px solid #293148;border-radius:10px;color:#b9c2dc;font-size:12px;line-height:1.5; }
        .footer-note { text-align:center;color:#69708d;font-size:10px;margin:18px 0 0; }
        @media (max-width:700px) {
          #studio { padding:13px;border-radius:16px; }
          .topbar { align-items:flex-start; }
          .brand-icon { width:45px;height:45px;border-radius:14px; }
          .pill { display:none; }
          .top-grid { grid-template-columns:1fr 1fr; }
          .top-grid .metric:first-child { grid-column:1 / -1; }
          .correction-grid,.download-grid { grid-template-columns:1fr; }
          .section { padding:13px; }
          .toolbar { align-items:flex-start; }
          select { min-width:0;width:100%; }
          .language-wrap { width:100%;align-items:flex-start; }
          .language-wrap label { padding-top:4px; }
          textarea { min-height:220px;font-size:13px; }
        }
      </style>

      <header class="topbar">
        <div class="brand">
          <div class="brand-icon">🎙️</div>
          <div>
            <h1>AI Voice Typewriter</h1>
            <div class="subtitle">Your voice, beautifully written.</div>
          </div>
        </div>
        <div class="pill">✦ AI-POWERED WORKSPACE</div>
      </header>

      <div class="top-grid">
        <div class="metric">
          <div class="metric-label">Workspace status</div>
          <div class="metric-value"><span id="statusDot" class="status-dot"></span><span id="statusShort">Ready to capture</span></div>
        </div>
        <div class="metric">
          <div class="metric-label">Words</div>
          <div class="metric-value" id="wordMetric">0</div>
        </div>
        <div class="metric">
          <div class="metric-label">Characters</div>
          <div class="metric-value" id="charMetric">0</div>
        </div>
      </div>

      <section class="section">
        <div class="section-head">
          <div class="section-title">▤ Transcript workspace</div>
          <div class="section-note">Auto-saves in this browser</div>
        </div>
        <div class="toolbar">
          <div class="language-wrap">
            <label for="language">TRANSCRIPTION LANGUAGE</label>
            <select id="language">
              <option value="en-IN">English (India)</option>
              <option value="hi-IN">Hindi (India)</option>
              <option value="en-US">English (US)</option>
            </select>
          </div>
          <div class="inline-actions">
            <button id="start" class="primary">🎙 Start voice typing</button>
            <button id="stop" class="stop">■ Stop</button>
          </div>
        </div>

        <div class="editor-wrap">
          <textarea id="output" placeholder="Click Start voice typing and speak naturally… or type directly here."></textarea>
          <div class="editor-footer">
            <span>✦ Your transcript stays editable</span>
            <span id="counter">0 words · 0 characters</span>
          </div>
        </div>
        <div class="inline-actions" style="margin-top:12px;">
          <button id="copy">▣ Copy transcript</button>
          <button id="clear">⌫ Clear text</button>
        </div>
        <div id="statusMessage" role="status" aria-live="polite">Ready when you are. Allow microphone access if your browser asks.</div>
      </section>

      <section class="section">
        <div class="section-head">
          <div class="section-title">✦ AI Correction Studio</div>
          <div class="section-note">Review before applying</div>
        </div>
        <p class="help">Polish your transcript with quick cleanup or Gemini AI grammar correction. Your original text remains unchanged until you apply the preview.</p>

        <div class="correction-grid">
          <div class="tool-card">
            <h3>✨ Basic cleanup</h3>
            <p>Fix extra spaces, punctuation spacing and basic English capitalization.</p>
            <button id="correctText" class="primary">Clean my text</button>
          </div>
          <div class="tool-card">
            <h3>🤖 Gemini AI correction</h3>
            <p>Improve grammar, spelling and sentence flow while preserving the original language.</p>
            <button id="aiCorrectText" class="ai-button">Correct with AI</button>
          </div>
        </div>

        <div class="preview-label">
          <div class="section-title" style="font-size:13px;">Corrected text preview</div>
          <span class="preview-chip">PREVIEW</span>
        </div>
        <div class="editor-wrap">
          <textarea id="correctedOutput" placeholder="Your corrected version will appear here. Review it before applying."></textarea>
          <div class="editor-footer"><span>Original transcript is protected</span><span>Editable preview</span></div>
        </div>
        <div class="inline-actions" style="margin-top:12px;">
          <button id="applyCorrection" class="success">✓ Use corrected text</button>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <div class="section-title">⇩ Export your transcript</div>
          <div class="section-note">Ready to save or share</div>
        </div>
        <p class="help">Download your current transcript as a UTF-8 text file or open the print dialog to save it as PDF.</p>
        <div class="download-grid">
          <button id="downloadTxt" class="download-card">
            <span class="file-icon">📄</span>
            <span><div class="download-title">Download TXT</div><div class="download-sub">Plain text · Hindi supported</div></span>
          </button>
          <button id="downloadPdf" class="download-card">
            <span class="file-icon">📕</span>
            <span><div class="download-title">Save as PDF</div><div class="download-sub">Print-ready A4 document</div></span>
          </button>
        </div>
      </section>
      <div class="footer-note">AI VOICE TYPEWRITER · YOUR WORDS, YOUR WORKFLOW</div>

      <script>
        const output = document.getElementById("output");
        const status = document.getElementById("statusMessage");
        const statusShort = document.getElementById("statusShort");
        const statusDot = document.getElementById("statusDot");
        const language = document.getElementById("language");
        const counter = document.getElementById("counter");
        const wordMetric = document.getElementById("wordMetric");
        const charMetric = document.getElementById("charMetric");
        const correctedOutput = document.getElementById("correctedOutput");
        const startButton = document.getElementById("start");
        const stopButton = document.getElementById("stop");
        const aiButton = document.getElementById("aiCorrectText");

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;
        let finalText = "";
        let isListening = false;

        function setStatus(message, shortMessage, live = false) {
          status.textContent = message;
          statusShort.textContent = shortMessage || (live ? "Listening live" : "Ready to capture");
          statusDot.classList.toggle("live", live);
        }

        try {
          output.value = localStorage.getItem("voiceTypewriterText") || "";
          finalText = output.value;
        } catch (error) {
          console.log("Browser storage is unavailable.");
        }

        function updateCounter() {
          const text = output.value;
          const words = text.trim() ? text.trim().split(/\s+/).length : 0;
          const chars = text.length;
          counter.textContent = words + " words · " + chars + " characters";
          wordMetric.textContent = words.toLocaleString();
          charMetric.textContent = chars.toLocaleString();
        }

        function saveTranscript() {
          try {
            localStorage.setItem("voiceTypewriterText", output.value);
          } catch (error) {
            setStatus("Auto-save is unavailable in this browser.", "Storage unavailable");
          }
        }

        output.addEventListener("input", () => {
          finalText = output.value;
          saveTranscript();
          updateCounter();
        });
        updateCounter();

        if (SpeechRecognition) {
          recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = language.value;

          language.addEventListener("change", () => {
            if (isListening) {
              setStatus("Stop voice typing before changing language.", "Stop to change language", true);
              return;
            }
            recognition.lang = language.value;
            setStatus("Language selected. You are ready to start.", "Ready to capture");
          });

          recognition.onstart = () => {
            isListening = true;
            startButton.disabled = true;
            stopButton.disabled = false;
            setStatus("Microphone active. Speak naturally; your words will appear below.", "Listening live", true);
          };

          recognition.onresult = (event) => {
            let interimText = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcript = event.results[i][0].transcript;
              if (event.results[i].isFinal) finalText += transcript + " ";
              else interimText += transcript;
            }
            output.value = finalText + interimText;
            saveTranscript();
            updateCounter();
          };

          recognition.onerror = (event) => {
            setStatus("Voice recognition error: " + event.error + ". Check microphone permission and try again.", "Microphone issue");
          };

          recognition.onend = () => {
            isListening = false;
            startButton.disabled = false;
            stopButton.disabled = false;
            finalText = output.value;
            setStatus("Voice typing stopped. Your transcript is saved in this browser.", "Capture paused");
          };

          startButton.onclick = () => {
            if (isListening) {
              setStatus("Voice typing is already active.", "Listening live", true);
              return;
            }
            recognition.lang = language.value;
            try {
              recognition.start();
            } catch (error) {
              setStatus("Could not start voice typing. Wait a moment and try again.", "Could not start");
            }
          };

          stopButton.onclick = () => {
            if (recognition && isListening) recognition.stop();
            else setStatus("Voice typing is already stopped.", "Capture paused");
          };
        } else {
          startButton.disabled = true;
          setStatus("Speech recognition is not supported in this browser. Please try Chrome.", "Browser not supported");
        }

        function cleanTranscript(text) {
          let result = text;
          result = result.replace(/\r\n/g, "\n");
          result = result.replace(/[ \t]+/g, " ");
          result = result.replace(/ *\n */g, "\n");
          result = result.trim();
          result = result.replace(/\s+([,.!?;:])/g, "$1");
          result = result.replace(/,{2,}/g, ",");
          result = result.replace(/([!?])\1{2,}/g, "$1$1");
          result = result.replace(/([,!?;:])(?=\S)/g, "$1 ");
          result = result.replace(/(\.)(?=[A-Za-z])/g, "$1 ");
          result = result.replace(/\bi\b/g, "I");
          result = result.replace(/(^|[.!?]\s+|\n\s*)([a-z])/g, (match, prefix, letter) => prefix + letter.toUpperCase());
          result = result.replace(/[ \t]+/g, " ");
          result = result.replace(/ *\n */g, "\n");
          return result.trim();
        }

        document.getElementById("correctText").onclick = () => {
          if (!output.value.trim()) {
            setStatus("Please enter or dictate some text first.", "Text needed");
            return;
          }
          correctedOutput.value = cleanTranscript(output.value);
          setStatus("Basic cleanup is ready. Review the preview before applying.", "Preview ready");
          correctedOutput.scrollIntoView({ behavior: "smooth", block: "center" });
        };

        aiButton.onclick = async () => {
          const originalText = output.value;
          if (!originalText.trim()) {
            setStatus("Please enter or dictate some text first.", "Text needed");
            return;
          }

          aiButton.disabled = true;
          setStatus("Gemini is polishing your transcript. This may take a moment.", "AI is working");
          try {
            const response = await fetch("http://127.0.0.1:8765/correct", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: originalText })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "AI correction failed.");
            if (typeof data.corrected_text !== "string" || !data.corrected_text.trim()) {
              throw new Error("Gemini returned no corrected text.");
            }
            correctedOutput.value = data.corrected_text;
            setStatus("AI correction is ready. Review the preview, then apply it if you like.", "AI preview ready");
            correctedOutput.scrollIntoView({ behavior: "smooth", block: "center" });
          } catch (error) {
            setStatus("AI correction unavailable: " + error.message + " Your original transcript is unchanged. Basic cleanup is still available.", "AI unavailable");
          } finally {
            aiButton.disabled = false;
          }
        };

        document.getElementById("applyCorrection").onclick = () => {
          if (!correctedOutput.value.trim()) {
            setStatus("Create a basic or AI correction preview first.", "Preview needed");
            return;
          }
          if (recognition && isListening) recognition.stop();
          output.value = correctedOutput.value;
          finalText = output.value;
          saveTranscript();
          updateCounter();
          setStatus("Corrected text applied to your main transcript.", "Text updated");
          output.scrollIntoView({ behavior: "smooth", block: "center" });
        };

        document.getElementById("copy").onclick = async () => {
          if (!output.value) {
            setStatus("There is no transcript to copy yet.", "Text needed");
            return;
          }
          try {
            await navigator.clipboard.writeText(output.value);
            setStatus("Transcript copied to clipboard.", "Copied");
          } catch (error) {
            output.focus();
            output.select();
            setStatus("Text selected. Press Ctrl+C to copy it.", "Manual copy");
          }
        };

        document.getElementById("clear").onclick = () => {
          if (recognition && isListening) recognition.stop();
          output.value = "";
          correctedOutput.value = "";
          finalText = "";
          try { localStorage.removeItem("voiceTypewriterText"); } catch (error) {}
          updateCounter();
          setStatus("Transcript and preview cleared.", "Workspace cleared");
        };

        document.getElementById("downloadTxt").onclick = () => {
          const text = output.value;
          if (!text.trim()) {
            setStatus("Please enter some text before downloading.", "Text needed");
            return;
          }
          const blob = new Blob(["\uFEFF", text], { type: "text/plain;charset=utf-8" });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = "voice_transcript.txt";
          document.body.appendChild(link);
          link.click();
          link.remove();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
          setStatus("Your TXT download has started.", "TXT export started");
        };

        document.getElementById("downloadPdf").onclick = () => {
          const text = output.value;
          if (!text.trim()) {
            setStatus("Please enter some text before saving a PDF.", "Text needed");
            return;
          }
          const printWindow = window.open("", "_blank");
          if (!printWindow) {
            setStatus("Popup blocked. Allow popups for this app and try again.", "Popup blocked");
            return;
          }
          const safeText = text.replace(/[&<>"']/g, (char) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
          })[char]);
          printWindow.document.open();
          printWindow.document.write(`
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8"><title>Transcript</title>
            <style>
              @page { size: A4; margin: 15mm; }
              html,body { margin:0;padding:0; }
              body { font-family:Arial,sans-serif;color:#222;font-size:12pt; }
              #transcript { white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.7; }
            </style></head><body>
            <div id="transcript">${safeText}</div>
            <script>window.onload=function(){window.focus();window.print();};<\/script>
            </body></html>
          `);
          printWindow.document.close();
          setStatus("In the print dialog, choose Save as PDF. Untick Headers and footers to hide date and time.", "PDF print dialog opened");
        };

        // Initial button state and initial counter.
        stopButton.disabled = true;
        setStatus("Ready when you are. Allow microphone access if your browser asks.", "Ready to capture");
      </script>
    </div>
    """,
    height=1750,
    scrolling=True,
)
