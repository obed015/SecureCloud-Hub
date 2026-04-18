import azure.functions as func

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SecureCloud Hub</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
    }
    header {
      background: #1a1d27;
      border-bottom: 1px solid #2d3748;
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    header h1 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #63b3ed;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: #1a2744;
      color: #63b3ed;
      font-size: 0.7rem;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      border: 1px solid #2d4a8a;
      margin-left: 0.5rem;
    }
    main {
      max-width: 900px;
      margin: 2rem auto;
      padding: 0 1rem;
    }
    .card {
      background: #1a1d27;
      border: 1px solid #2d3748;
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card h2 {
      font-size: 0.9rem;
      font-weight: 600;
      color: #a0aec0;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 1rem;
    }
    input[type="file"] {
      display: block;
      margin-bottom: 1rem;
      color: #e2e8f0;
    }
    button {
      background: #2b6cb0;
      color: white;
      border: none;
      padding: 0.6rem 1.2rem;
      border-radius: 6px;
      font-size: 0.85rem;
      cursor: pointer;
    }
    button:hover { background: #3182ce; }
    button:disabled { background: #2d3748; cursor: not-allowed; }
    .btn-secondary {
      background: #2d3748;
      font-size: 0.8rem;
      padding: 0.4rem 0.8rem;
    }
    .btn-secondary:hover { background: #4a5568; }
    #status {
      margin-top: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      display: none;
    }
    .status-success {
      background: #1a3a2a;
      border: 1px solid #276749;
      color: #68d391;
      display: block !important;
    }
    .status-error {
      background: #3a1a1a;
      border: 1px solid #742a2a;
      color: #fc8181;
      display: block !important;
    }
    .status-loading {
      background: #1a2744;
      border: 1px solid #2d4a8a;
      color: #63b3ed;
      display: block !important;
    }
    .file-list { list-style: none; }
    .file-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 0;
      border-bottom: 1px solid #2d3748;
    }
    .file-item:last-child { border-bottom: none; }
    .file-info { flex: 1; }
    .file-name {
      font-size: 0.9rem;
      color: #e2e8f0;
      font-weight: 500;
    }
    .file-meta {
      font-size: 0.75rem;
      color: #718096;
      margin-top: 0.2rem;
    }
    .scan-badge {
      font-size: 0.7rem;
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      margin-right: 1rem;
      background: #1a3a2a;
      color: #68d391;
      border: 1px solid #276749;
    }
    .sas-link {
      display: block;
      margin-top: 0.5rem;
      font-size: 0.75rem;
      color: #63b3ed;
      word-break: break-all;
      text-decoration: none;
      background: #0f1a2d;
      padding: 0.4rem 0.6rem;
      border-radius: 4px;
      border: 1px solid #2d4a8a;
    }
    .expiry-note {
      font-size: 0.7rem;
      color: #718096;
      margin-top: 0.25rem;
    }
    .empty-state {
      text-align: center;
      padding: 2rem;
      color: #718096;
      font-size: 0.9rem;
    }
    .user-bar {
      background: #1a2744;
      border: 1px solid #2d4a8a;
      border-radius: 6px;
      padding: 0.6rem 1rem;
      font-size: 0.8rem;
      color: #63b3ed;
      margin-bottom: 1rem;
    }
  </style>
</head>
<body>
<header>
  <h1>SecureCloud Hub</h1>
  <div>
    <span class="badge">Zero-trust</span>
    <span class="badge">Direct-to-Blob upload</span>
    <span class="badge">Flex Functions</span>
  </div>
</header>

<main>
  <div class="card">
    <h2>Upload file</h2>
    <input type="file" id="file-input">
    <button id="upload-btn" onclick="uploadFile()">Upload securely</button>
    <div id="status"></div>
  </div>

  <div class="card">
    <h2>Your clean files</h2>
    <div id="user-bar" class="user-bar" style="display:none"></div>
    <button class="btn-secondary" onclick="loadFiles()">Refresh</button>
    <ul class="file-list" id="file-list">
      <div class="empty-state">Loading your files...</div>
    </ul>
  </div>
</main>

<script>
  document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
  });

  async function uploadFile() {
    const input = document.getElementById('file-input');
    const file = input.files[0];

    if (!file) {
      setStatus('Please select a file first.', 'error');
      return;
    }

    setStatus('Requesting secure upload URL...', 'loading');

    try {
      const requestRes = await fetch('/api/request-upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileName: file.name,
          fileSize: file.size,
          contentType: file.type || 'application/octet-stream'
        })
      });

      const requestData = await requestRes.json();

      if (!requestRes.ok) {
        throw new Error(requestData.error || 'Failed to request upload URL');
      }

      setStatus('Uploading directly to Azure Blob Storage...', 'loading');

      const uploadRes = await fetch(requestData.uploadUrl, {
        method: 'PUT',
        headers: {
          'x-ms-blob-type': 'BlockBlob',
          'Content-Type': file.type || 'application/octet-stream'
        },
        body: file
      });

      if (!uploadRes.ok) {
        throw new Error('Direct upload to Blob Storage failed');
      }

      setStatus(
        'Upload completed. The file is now being scanned. Refresh your file list in 20-30 seconds.',
        'success'
      );

      input.value = '';
    } catch (err) {
      setStatus('Upload failed: ' + err.message, 'error');
    }
  }

  async function loadFiles() {
    const list = document.getElementById('file-list');
    list.innerHTML = '<div class="empty-state">Loading...</div>';

    try {
      const res = await fetch('/api/files');
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to load files');
      }

      const userBar = document.getElementById('user-bar');
      userBar.textContent = 'Signed in as: ' + data.user;
      userBar.style.display = 'block';

      if (!data.files || data.files.length === 0) {
        list.innerHTML = '<div class="empty-state">No clean files available yet.</div>';
        return;
      }

      list.innerHTML = '';
      data.files.forEach(file => {
        const item = document.createElement('li');
        item.className = 'file-item';
        item.innerHTML = `
          <div class="file-info">
            <div class="file-name">${escapeHtml(file.name)}</div>
            <div class="file-meta">
              ${formatSize(file.size)} · ${formatDate(file.lastModified)}
            </div>
            <div id="link-${btoa(file.fullName)}"></div>
          </div>
          <div style="display:flex;align-items:center">
            <span class="scan-badge">✓ Clean</span>
            <button class="btn-secondary" onclick="getDownloadLink('${escapeHtml(file.fullName)}', '${btoa(file.fullName)}')">
              Get link
            </button>
          </div>
        `;
        list.appendChild(item);
      });

    } catch (err) {
      list.innerHTML = '<div class="empty-state" style="color:#fc8181">Failed to load files: ' + err.message + '</div>';
    }
  }

  async function getDownloadLink(fullName, encodedName) {
    const container = document.getElementById('link-' + encodedName);
    container.innerHTML = '<span style="font-size:0.75rem;color:#63b3ed">Generating secure link...</span>';

    try {
      const res = await fetch('/api/download?fileName=' + encodeURIComponent(fullName));
      const text = await res.text();

      if (!res.ok) {
        throw new Error(text);
      }

      const expiry = new Date(Date.now() + 15 * 60 * 1000);

      container.innerHTML = `
        <a href="${text}" target="_blank" class="sas-link">
          Click to download
        </a>
        <div class="expiry-note">
          Link expires at ${expiry.toLocaleTimeString()}
        </div>
      `;

      setTimeout(() => {
        container.innerHTML = '<div class="expiry-note" style="color:#fc8181">Link expired. Generate a new one.</div>';
      }, 15 * 60 * 1000);

    } catch (err) {
      container.innerHTML = '<div class="expiry-note" style="color:#fc8181">Failed: ' + err.message + '</div>';
    }
  }

  function setStatus(message, type) {
    const el = document.getElementById('status');
    el.className = type ? 'status-' + type : '';
    el.textContent = message;
    el.style.display = message ? 'block' : 'none';
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function formatDate(iso) {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
</script>
</body>
</html>
"""

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        HTML,
        status_code=200,
        mimetype="text/html"
    )
