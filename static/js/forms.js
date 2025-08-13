const codeCount = document.getElementById('charCounter')
const textArea = document.querySelector('textarea[name="code"]')
const maxlength = textArea.getAttribute("maxlength")

const numChar = textArea.value.length;
codeCount.textContent = `${numChar} / ${maxlength}`;

textArea.addEventListener('input', () => {
    const numChar = textArea.value.length;
    codeCount.textContent = `${numChar} / ${maxlength}`;

    codeCount.classList.remove('green', 'yellow', 'red')

    if (numChar < 4000) {
        codeCount.classList.add('green');
    } else if (numChar <= 4500) {
        codeCount.classList.add('yellow');
    } else {
        codeCount.classList.add('red');
    }
})

// Ключ для хранения черновика
const formDataKey = 'myFormDraft';

// 1. Сохранение данных формы (черновика) каждые 5 секунд
function saveDraft() {
    const name = document.querySelector('input[name="name"]');
    const lang = document.querySelector('select[name="lang"]');
    const code = document.querySelector('textarea[name="code"]');

    if (!name.value.trim() && !lang.value.trim() && !code.value.trim()) {
        return;
    }
    const formData = {
        name: name.value,
        lang: lang.value,
        code: code.value,
    };

    localStorage.setItem(formDataKey, JSON.stringify(formData));

    const saveIcon = document.getElementById('saveIcon');
    saveIcon.style.display = 'inline-block';
    saveIcon.style.color = 'green';
    setTimeout(() => {
        saveIcon.style.color = 'gray';
    }, 5000);
}

setInterval(saveDraft, 5000);

// 2. Восстановление черновика из localStorage
function restoreDraft() {
    const data = localStorage.getItem(formDataKey);
    if (!data)
        return;
    const formData = JSON.parse(data);

    const name = document.querySelector('input[name="name"]');
    const lang = document.querySelector('select[name="lang"]');
    const code = document.querySelector('textarea[name="code"]');
    name.value = formData.name;
    lang.value = formData.lang;
    code.value = formData.code;
    // Скрываем окно с подсказкой
    const alertElement = document.querySelector('#promptDiv');
    if (alertElement) {
        alertElement.remove();
    }
    if (typeof sendMessage === 'function') {
        sendMessage("Данные формы восстановлены");
    }
}

setInterval(saveDraft, 5000);

// 3. Проверки данных формы

function checkDraft() {
    const data = localStorage.getItem(formDataKey);

    console.log("checkDraft called");
    console.log("data:", data);

    // Показываем подсказку только если есть данные и пользователь не отказался
    if (data) {
        console.log('Există date:', data);
        showRestorePrompt()
    } else {
        console.log('Nu există date sau este gol');
    }
}

function showRestorePrompt() {
    if (document.getElementById('promptDiv')) return; // чтобы не создавать повторно

    const promptDiv = document.createElement('div');
    promptDiv.className = 'alert alert-info alert-dismissible fade show';
    promptDiv.setAttribute("id", "promptDiv");
    promptDiv.innerHTML = `
        <strong>Найден черновик!</strong> 
        Хотите восстановить сохранённые данные?
        <button type="button" class="btn btn-secondary btn-sm ms-2" onclick="restoreDraft()">
            Восстановить черновик
        </button>
        <button type="button" class="btn btn-secondary btn-sm ms-2" onclick="discardDraft()">
            Отменить
        </button>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const titleRow = document.querySelector('.row:first-child');
    if (titleRow) {
        titleRow.parentNode.insertBefore(promptDiv, titleRow.nextSibling);
    }
}

function discardDraft() {
    localStorage.removeItem(formDataKey);

    const alertElement = document.querySelector('#promptDiv');
    if (alertElement) {
        alertElement.remove();
    }
    const name = document.querySelector('input[name="name"]');
    const lang = document.querySelector('select[name="lang"]');
    const code = document.querySelector('textarea[name="code"]');

    if (name) name.value = '';
    if (lang) lang.value = '';
    if (code) code.value = '';
}

document.addEventListener('DOMContentLoaded', function () {
    checkDraft();

    const form = document.querySelector('form');
    form.addEventListener('submit', function () {
        localStorage.removeItem(formDataKey);
    });
});