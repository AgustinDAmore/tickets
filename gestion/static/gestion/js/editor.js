// Contenido para gestion/static/gestion/js/editor.js

document.addEventListener('DOMContentLoaded', function() {
    const toolbars = document.querySelectorAll('.toolbar');

    toolbars.forEach(toolbar => {
        const targetTextareaId = toolbar.getAttribute('data-editor-for');
        if (!targetTextareaId) return;

        const cuerpoTextarea = document.getElementById(targetTextareaId);
        const previewDiv = document.getElementById(targetTextareaId + '-preview');

        if (!cuerpoTextarea || !previewDiv) {
            console.error(`Editor no pudo inicializarse para el textarea con id: ${targetTextareaId}`);
            return;
        }

        const textColorPicker = toolbar.querySelector('.text-color-picker');
        const highlightColorPicker = toolbar.querySelector('.highlight-color-picker');

        function applyInlineFormats(text) {
            return text.replace(/N\((.*?)\)/g, '<strong>$1</strong>')
                       .replace(/I\((.*?)\)/g, '<em>$1</em>')
                       .replace(/S\((.*?)\)/g, '<u>$1</u>')
                       .replace(/T\((.*?)\)/g, '<s>$1</s>')
                       .replace(/M\(([^,)]+),([^)]+)\)/g, '<mark style="background-color:$1;">$2</mark>')
                       .replace(/C\(([^,]+),([^)]+)\)/g, '<span style="color:$1">$2</span>')
                       .replace(/url\((.*?)\)/g, '<a href="$1" target="_blank" class="text-indigo-600 hover:underline">$1</a>');
        }

        function updatePreview() {
            let text = cuerpoTextarea.value;
            const lines = text.split('\n');
            let html = '';
            let inUl = false, inOl = false;
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine) {
                    if (inUl || inOl) {
                        if (inUl) { html += '</ul>'; inUl = false; }
                        if (inOl) { html += '</ol>'; inOl = false; }
                    }
                    continue;
                }
                if (trimmedLine.startsWith('* ')) {
                    if (inOl) { html += '</ol>'; inOl = false; }
                    if (!inUl) { html += '<ul>'; inUl = true; }
                    html += `<li>${applyInlineFormats(trimmedLine.substring(2))}</li>`;
                } else if (/^\d+\.\s/.test(trimmedLine)) {
                    if (inUl) { html += '</ul>'; inUl = false; }
                    if (!inOl) { html += '<ol>'; inOl = true; }
                    html += `<li>${applyInlineFormats(trimmedLine.replace(/^\d+\.\s/, ''))}</li>`;
                } else {
                    if (inUl) { html += '</ul>'; inUl = false; }
                    if (inOl) { html += '</ol>'; inOl = false; }
                    html += `<p>${applyInlineFormats(line)}</p>`;
                }
            }
            if (inUl) html += '</ul>'; if (inOl) html += '</ol>';
            previewDiv.innerHTML = html;
        }

        toolbar.addEventListener('click', function(e) {
            let target = e.target.closest('button');
            if (!target || !target.dataset.format) return;

            const format = target.dataset.format;
            const start = cuerpoTextarea.selectionStart;
            const end = cuerpoTextarea.selectionEnd;
            const selectedText = cuerpoTextarea.value.substring(start, end) || 'texto';
            let replacement = '';
            switch (format) {
                case 'N': case 'I': case 'S': case 'T':
                    replacement = `${format.toUpperCase()}(${selectedText})`; break;
                case 'M':
                    replacement = `M(${highlightColorPicker.value}, ${selectedText})`; break;
                case 'C':
                    replacement = `C(${textColorPicker.value}, ${selectedText})`; break;
                case 'url':
                    replacement = `url(${selectedText === 'texto' ? 'https://ejemplo.com' : selectedText})`; break;
                case 'lista': replacement = `\n* Item 1\n* Item 2`; break;
                case 'lista-num': replacement = `\n1. Item 1\n2. Item 2`; break;
            }
            if (replacement) {
                cuerpoTextarea.setRangeText(replacement, start, end, 'end');
                cuerpoTextarea.focus();
                cuerpoTextarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        cuerpoTextarea.addEventListener('input', updatePreview);
        updatePreview();
    });
});