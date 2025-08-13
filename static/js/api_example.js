// Функция для отправки GET запроса к API
function fetchApiData() {
    // Отправляем GET запрос к API endpoint
    fetch('/api/simple-data/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        // Проверяем статус ответа
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }

        // Парсим JSON ответ
        return response.json();
    })
    .then(function(data) {
        // Обрабатываем полученные данные
        console.log('Полученные данные:', data);

        // Пример обработки данных
        if (data.success) {
            displayData(data.message);
        } else {
            console.error('Ошибка API:', data.error);
        }
    })
    .catch(function(error) {
        console.error('Ошибка при отправке запроса:', error);
    });
}

// Функция для отображения данных на странице
function displayData(message) {
    const container = document.getElementById('api-result');
    if (container) {
        container.innerHTML = '<p>Ответ от API: ' + message + '</p>';
    }
}

// Функция для отправки POST запроса (опционально)
function sendPostRequest(data) {
    return fetch('/api/simple-data/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('HTTP error! status: ' + response.status);
        }
        return response.json();
    })
    .then(function(result) {
        console.log('POST ответ:', result);
        return result;
    })
    .catch(function(error) {
        console.error('Ошибка при отправке POST запроса:', error);
    });
}

// Вызываем функцию при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем кнопку для тестирования API
    const button = document.createElement('button');
    button.textContent = 'Получить данные от API';
    button.onclick = fetchApiData;

    const container = document.getElementById('api-container');
    if (container) {
        container.appendChild(button);

        // Создаем контейнер для результатов
        const resultDiv = document.createElement('div');
        resultDiv.id = 'api-result';
        container.appendChild(resultDiv);
    }
});