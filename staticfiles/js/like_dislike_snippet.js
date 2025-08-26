document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.snippet-like, .snippet-dislike').forEach(btn => {
        btn.addEventListener("click", function (e) {
             e.preventDefault();
            const snippetId = this.dataset.snippetId;   // schimbat aici
            const vote = this.classList.contains('snippet-like') ? 1 : -1;

            fetch("/api/snippet/like/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify({
                    snippet_id: snippetId,
                    vote: vote
                })
            })
            .then(response => response.json())
            .then(data => {
                document.querySelector(`#snippet-likes-${snippetId}`).textContent = data.likes_count;
                document.querySelector(`#snippet-dislikes-${snippetId}`).textContent = data.dislikes_count;
            })
            .catch(error => console.error("Error:", error));
        });
    });
});