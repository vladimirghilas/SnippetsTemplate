const alertsBox = document.getElementById('alertsFixedContainer');

// function closeMessage() {
//     const message = alertsBox.querySelector('div');
//     message.remove();
// }
//
// function closeMessages() {
//     const messages = alertsBox.querySelectorAll('div');
//
//     let step = 600;
//     let messageNum = 1
//     for (let message of messages) {
//         setTimeout(closeMessage, messageNum * step);
//         messageNum++;
//     }
// }

function closeMessages() {
    const messages = alertsBox.querySelectorAll('div');

    messages.forEach((message, index) => {
        setTimeout(() => {
            message.remove();
        }, index * 600);
    });
}

 function sendMessage(text, type = 'info') {
     const message = document.createElement('div');
     message.classList.add('alert', 'alert-dismissible', 'fade', 'show');
     message.classList.add(`alert-${type}`);
     message.setAttribute('role', 'alert');
     message.innerHTML = `${text} <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>`;
     alertsBox.appendChild(message);
     setTimeout(closeMessages, 2000);
 }

setTimeout(closeMessages, 2000);