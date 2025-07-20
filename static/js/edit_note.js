document.addEventListener("DOMContentLoaded", () => {
  const filename = window.noteFilename; // undefined on new-note
  const autosaveInterval = 5000;
  let saveTimeout;

  const contentEl = document.getElementById("content");
  const previewEl = document.getElementById("preview");
  const editorEl = document.getElementById("editor");
  const saveStatus = document.getElementById("save-status");

  let lastContent = contentEl.value;

  function stripFrontmatter(text) {
    if (text.startsWith("---")) {
      const endIndex = text.indexOf("---", 3);
      if (endIndex !== -1) return text.slice(endIndex + 3).trim();
    }
    return text.trim();
  }

  function convertInternalLinks(text) {
    return text.replace(/\[\[([^\]]+)\]\]/g, (_, p1) => {
      const link = `/notes/${encodeURIComponent(p1.trim())}.md`;
      return `<a href="${link}" class="text-green-400 underline hover:text-green-300">${p1.trim()}</a>`;
    });
  }

  function updatePreview() {
    const rawText = contentEl.value;
    const stripped = stripFrontmatter(rawText);
    previewEl.innerHTML = marked.parse(stripped);
  }

  function toggleSection(id) {
    const el = document.getElementById(id);
    el.classList.toggle("hidden");
    updateSectionLayout();
  }

  function updateSectionLayout() {
    const editorVisible = !editorEl.classList.contains("hidden");
    const previewVisible = !previewEl.classList.contains("hidden");

    editorEl.classList.remove("col-span-2");
    previewEl.classList.remove("col-span-2");

    if (editorVisible && previewVisible) {
      editorEl.classList.remove("full-width");
      previewEl.classList.remove("full-width");
    } else if (editorVisible) {
      editorEl.classList.add("col-span-2");
      previewEl.classList.remove("col-span-2");
    } else if (previewVisible) {
      previewEl.classList.add("col-span-2");
      editorEl.classList.remove("col-span-2");
    }
  }

  function showSaveStatus() {
    if (!saveStatus) return;
    saveStatus.style.opacity = 1;
    setTimeout(() => {
      saveStatus.style.opacity = 0;
    }, 2000);
  }

  async function autoSave() {
    let currentContent = contentEl.value;
    if (currentContent !== lastContent) {
      fetch(`/autosave-note/${VIRTUAL_PATH}`, {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          },
          body: JSON.stringify({ content: currentContent })
      })
      .then(res => res.json())
      .then(data => {
          if (data.status === "ok") {
              lastSaved = currentContent;
              showSaveStatus();
          } else {
              console.error("Auto-save failed:", data.message);
          }
      })
      .catch(err => console.error("Auto-save error:", err))
      .finally(() => {
          isSaving = false;
      });
    }
  }

  // Bind events
  document.getElementById("toggle-editor")?.addEventListener("click", () => toggleSection("editor"));
  document.getElementById("toggle-preview")?.addEventListener("click", () => toggleSection("preview"));
  contentEl.addEventListener("input", updatePreview);
  editorEl.addEventListener("input", () => {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(autoSave, autosaveInterval);
});

  // Initial setup
  updatePreview();
  updateSectionLayout();
  saveStatus.style.opacity = 0;

  if (filename) {
    setInterval(autoSave, autosaveInterval);
  }
});
