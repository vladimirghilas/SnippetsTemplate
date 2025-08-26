const commentForm = document.getElementById('commentForm');
const commentInput = document.getElementById("commentInput");
const charCount = document.getElementById("charCount");
const submitBtn = commentForm.querySelector('button[type="submit"]');

const MAX_LENGTH = 500;

function validateComment() {
    const value = commentInput.value.trim();
    const length = commentInput.value.length;
    charCount.textContent = `${length}/${MAX_LENGTH}`;
    submitBtn.disabled = !(value.length > 0 && length <= MAX_LENGTH);
}

validateComment();
commentInput.addEventListener('input', validateComment);