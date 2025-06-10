document.addEventListener("DOMContentLoaded", () => {
    const filename = window.noteFilename;
    const autosaveInterval = 5000;

    const contentEl = document.getElementById('content');
    let lastContent = contentEl.value;

    function stripFrontmatter(text) {
        if (text.startsWith('---')) {
            const endIndex = text.indexOf('---', 3);
            if (endIndex !== -1) return text.slice(endIndex + 3).trim();
        }
        return text;
    }

    function convertInternalLinks(text) {
        return text.replace(/\[\[([^\]]+)\]\]/g, (_, p1) => {
            const link = `/notes/${encodeURIComponent(p1.trim())}.md`;
            return `<a href="${link}">${p1.trim()}</a>`;
        });
    }

    function updatePreview() {
        const rawMarkdown = contentEl.value;
        const cleanMarkdown = convertInternalLinks(stripFrontmatter(rawMarkdown));
        document.getElementById('preview').innerHTML = marked.parse(cleanMarkdown);
    }

    function toggleSection(id) {
        const el = document.getElementById(id);
        el.style.display = (el.style.display === 'none') ? 'block' : 'none';
        updateSectionLayout();
    }

    function updateSectionLayout() {
        const editor = document.getElementById('editor');
        const preview = document.getElementById('preview');

        const editorVisible = editor.style.display !== 'none';
        const previewVisible = preview.style.display !== 'none';

        if (editorVisible && previewVisible) {
            editor.classList.remove('full-width');
            preview.classList.remove('full-width');
        } else if (editorVisible) {
            editor.classList.add('full-width');
            preview.classList.remove('full-width');
        } else if (previewVisible) {
            preview.classList.add('full-width');
            editor.classList.remove('full-width');
        }
    }


    function showSaveStatus() {
        const status = document.getElementById('save-status');
        status.style.opacity = 1;
        setTimeout(() => {
            status.style.opacity = 0;
        }, 2000);
    }

    async function autoSave() {
        const currentContent = contentEl.value;
        if (currentContent !== lastContent) {
            try {
                const response = await fetch(`/autosave-note/${filename}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: currentContent })
                });
                if (response.ok) {
                    lastContent = currentContent;
                    showSaveStatus();
                } else {
                    console.error("Autosave failed");
                }
            } catch (err) {
                console.error("Autosave error:", err);
            }
        }
    }

    document.getElementById('toggle-editor').addEventListener('click', () => toggleSection('editor'));
    document.getElementById('toggle-preview').addEventListener('click', () => toggleSection('preview'));
    contentEl.addEventListener('input', updatePreview);

    updatePreview();
    updateSectionLayout();
    if (window.noteFilename) {
        setInterval(autoSave, autosaveInterval);
    }
});
