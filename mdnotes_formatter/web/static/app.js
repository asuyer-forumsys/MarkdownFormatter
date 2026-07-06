const fileListEl = document.getElementById("fileList");
const statusEl = document.getElementById("status");
const selectedPathEl = document.getElementById("selectedPath");
const renameInfoEl = document.getElementById("renameInfo");
const leftPaneEl = document.getElementById("leftPane");
const rightPaneEl = document.getElementById("rightPane");
const formatBtnEl = document.getElementById("formatBtn");
const refreshBtnEl = document.getElementById("refreshBtn");
const rootInputEl = document.getElementById("rootInput");

let selectedFile = null;
let latestPreview = null;

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function asJson(response) {
  if (!response.ok) {
    return response.json().then((data) => {
      const message = data?.error || `HTTP ${response.status}`;
      throw new Error(message);
    });
  }
  return response.json();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function highlightMarkdownLine(line) {
  if (window.hljs?.highlight) {
    return window.hljs.highlight(line, { language: "markdown" }).value;
  }
  return escapeHtml(line);
}

function renderCodePane(target, content, changedLines, sideClass) {
  const lines = content.split(/\r?\n/);
  if (lines.length > 0 && lines[lines.length - 1] === "") {
    lines.pop();
  }

  const changed = new Set(changedLines || []);
  const html = lines
    .map((line, index) => {
      const lineNumber = index + 1;
      const lineClass = changed.has(lineNumber) ? `code-line ${sideClass}` : "code-line";
      const highlightedLine = highlightMarkdownLine(line);
      return `
        <div class="${lineClass}">
          <span class="line-no">${lineNumber}</span>
          <div class="line-code"><code class="line-code-inner language-markdown">${highlightedLine || " "}</code></div>
        </div>
      `;
    })
    .join("");

  target.innerHTML =
    html ||
    '<div class="code-line"><span class="line-no">1</span><div class="line-code"><code class="line-code-inner language-markdown"> </code></div></div>';
}

function renderFileList(files) {
  fileListEl.innerHTML = "";
  files.forEach((path) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.textContent = path;
    button.title = path;
    button.className = selectedFile === path ? "active" : "";
    button.addEventListener("click", () => selectFile(path));
    li.appendChild(button);
    fileListEl.appendChild(li);
  });
}

async function refreshFiles() {
  const root = rootInputEl.value.trim();
  const query = root ? `?root=${encodeURIComponent(root)}` : "";

  try {
    setStatus("Loading files…");
    const payload = await fetch(`/api/files${query}`).then(asJson);
    renderFileList(payload.files || []);
    setStatus(`Loaded ${payload.files.length} markdown files`);
  } catch (error) {
    setStatus(`Failed to load files: ${error.message}`, true);
  }
}

async function selectFile(path) {
  selectedFile = path;
  latestPreview = null;
  formatBtnEl.disabled = true;

  document.querySelectorAll("#fileList button").forEach((btn) => {
    btn.classList.toggle("active", btn.textContent === path);
  });

  selectedPathEl.textContent = path;
  renameInfoEl.textContent = "Loading preview…";
  renameInfoEl.className = "";

  try {
    const preview = await fetch("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    }).then(asJson);

    latestPreview = preview;
    renderCodePane(leftPaneEl, preview.original_content, preview.changed_left_lines, "changed-left");
    renderCodePane(rightPaneEl, preview.formatted_content, preview.changed_right_lines, "changed-right");

    if (preview.renamed) {
      renameInfoEl.textContent = `Will rename to: ${preview.updated_path}`;
      renameInfoEl.className = "warn";
    } else {
      renameInfoEl.textContent = "Filename will remain unchanged.";
      renameInfoEl.className = "ok";
    }

    formatBtnEl.disabled = false;
    setStatus(`Preview ready for ${path}`);
  } catch (error) {
    renameInfoEl.textContent = `Preview failed: ${error.message}`;
    renameInfoEl.className = "error";
    setStatus(`Preview failed: ${error.message}`, true);
  }
}

async function formatSelectedFile() {
  if (!selectedFile) return;
  formatBtnEl.disabled = true;

  try {
    setStatus("Applying format…");
    const result = await fetch("/api/format", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: selectedFile }),
    }).then(asJson);

    selectedFile = result.updated_path;
    setStatus(`Formatted: ${result.updated_path}`);

    await refreshFiles();
    await selectFile(result.updated_path);
  } catch (error) {
    setStatus(`Format failed: ${error.message}`, true);
    formatBtnEl.disabled = false;
  }
}

refreshBtnEl.addEventListener("click", refreshFiles);
formatBtnEl.addEventListener("click", formatSelectedFile);

refreshFiles();
