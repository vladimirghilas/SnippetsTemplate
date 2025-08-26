document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.btn-like, .btn-dislike').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            const vote = this.classList.contains('btn-like') ? 1 : -1;

            fetch('/api/comment/like/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({ comment_id: commentId, vote: vote })
            })
            .then(response => response.json())
            .then(data => {
                document.querySelector(`#likes-${commentId}`).textContent = data.likes_count;
                document.querySelector(`#dislikes-${commentId}`).textContent = data.dislikes_count;
            })
            .catch(error => console.error('Error:', error));
        });
    });
});