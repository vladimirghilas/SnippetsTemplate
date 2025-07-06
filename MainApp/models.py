from django.db import models
from django.contrib.auth.models import User

LANG_CHOICES = [
    ("python", "Python"),
    ("cpp", "C++"),
    ("java", "Java"),
    ("javascript", "JavaScript")
]

# <i class="fa-brands fa-python"></i>
LANG_ICONS = {
    "python": "fa-python",
    "javascript": "fa-js",
    "java": "fa-java",
}
class Snippet(models.Model):
    class Meta:
        ordering = ['name', 'lang']

    name = models.CharField(max_length=100)
    lang = models.CharField(max_length=30,choices=LANG_CHOICES)
    code = models.TextField(max_length=5000)
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    public = models.BooleanField(default=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)

class Comment(models.Model):
    text = models.TextField(verbose_name="Текст комментария")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    author = models.ForeignKey(User,
            on_delete=models.SET_NULL, null=True, related_name='comments',verbose_name="Автор")
    snippet = models.ForeignKey(Snippet,
            on_delete=models.CASCADE, related_name='comments',verbose_name="Сниппет")

    def __str__(self):
        return f"Комментарий от {self.author.username} к «{self.snippet.name}»"
