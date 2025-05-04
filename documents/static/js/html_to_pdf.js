function adjustPreviewHeight() {
    const textArea = document.getElementById('text-editor');
    const previewBox = document.getElementById('html-preview');
    previewBox.style.height = `${textArea.offsetHeight}px`;
}

window.addEventListener('load', adjustPreviewHeight);
window.addEventListener('resize', adjustPreviewHeight);
function insertTag(tag) {
    const textarea = document.getElementById('text-editor');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;

    const before = text.substring(0, start);
    const after = text.substring(end, text.length);
    const selectedText = text.substring(start, end);

    textarea.value = `${before}<${tag}>${selectedText}</${tag}>${after}`;
    textarea.focus();
    textarea.setSelectionRange(start + tag.length + 2, end + tag.length + 2);

    updatePreview();
}

function insertTable() {
    const rows = document.getElementById('table-rows').value;
    const cols = document.getElementById('table-cols').value;
    const textarea = document.getElementById('text-editor');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;

    const before = text.substring(0, start);
    const after = text.substring(end, text.length);

    let tableText = '<table border="1" cellpadding="5" cellspacing="0">\n';
    for (let i = 0; i < rows; i++) {
        tableText += '  <tr>\n';
        for (let j = 0; j < cols; j++) {
            tableText += `    <td>Ячейка ${i + 1}, ${j + 1}</td>\n`;
        }
        tableText += '  </tr>\n';
    }
    tableText += '</table>\n';

    textarea.value = `${before}${tableText}${after}`;
    textarea.focus();
    textarea.setSelectionRange(start + tableText.length, start + tableText.length);

    updatePreview();
}

function updatePreview() {
    const textarea = document.getElementById('text-editor');
    const preview = document.getElementById('html-preview');

    preview.innerHTML = textarea.value;
}
async function uploadDocument() {
    const textarea = document.getElementById('text-editor');
    const htmlContent = textarea.value;
    const documentTitle = document.getElementById('document-title').value || 'document';

    const uploadUrl = "{{ url('upload_document') }}";

    try {
        const formData = new FormData();
        formData.append('file_content', htmlContent);
        formData.append('title', documentTitle);

        const response = await fetch(uploadUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            }
        });

        if (response.ok) {
            alert('PDF успешно загружен!');
            const responseData = await response.json();
            window.location.href = responseData.redirect_url;
        } else {
            const errorText = await response.text();
            console.error('Ошибка при загрузке PDF:', errorText);
            alert('Ошибка при загрузке PDF. Пожалуйста, попробуйте снова.');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке запроса.');
    }
}
