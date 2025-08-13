function copyToBuffer(text) {
    console.log("copy");
    navigator.clipboard.writeText(text)
        .then(function () {
            // Этот код выполнится, если промис разрешился (успешное копирование)
            // alert('Текст успешно скопирован!');
            sendMessage('Код скопирован!');
        })
        .catch(function (err) {
            // Этот код выполнится, если промис был отклонён (ошибка копирования)
            console.error('Ошибка копирования:', err);
            alert('Не удалось скопировать текст. Проверьте консоль.');
        });
}
