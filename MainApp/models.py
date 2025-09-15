from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.db.models import ManyToManyField
from django.db.models.fields import CharField

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

User._meta.get_field('email')._unique = True


class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTES = (
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    )

    vote = models.SmallIntegerField(choices=VOTES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']


class Tag(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        constraints = [UniqueConstraint(Lower('name'), name='unique_lower_tag_name')]

    def __str__(self):
        return f"Tag: {self.name}"


class Snippet(models.Model):
    class Meta:
        ordering = ['name', 'lang']
        indexes = [
            models.Index(fields=['name', 'lang']),
            models.Index(fields=['lang', 'name']),
            models.Index(fields=['user', 'name', 'lang']),
        ]

    name = models.CharField(max_length=100)
    lang = models.CharField(max_length=30, choices=LANG_CHOICES)
    code = models.TextField(max_length=5000)
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    public = models.BooleanField(default=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    tags = models.ManyToManyField(to=Tag, blank=True)
    likes = GenericRelation(LikeDislike)

    def __repr__(self):
        return f"S: {self.name}|{self.lang} views:{self.views_count} public:{self.public} user:{self.user}"

    def likes_count(self):
        return self.likes.filter(vote=LikeDislike.LIKE).count()

    def dislikes_count(self):
        return self.likes.filter(vote=LikeDislike.DISLIKE).count()

class Comment(models.Model):
    text = models.TextField(verbose_name="Текст комментария")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    author = models.ForeignKey(User,
                               on_delete=models.SET_NULL, null=True, related_name='comments', verbose_name="Автор")
    snippet = models.ForeignKey(Snippet,
                                on_delete=models.CASCADE, related_name='comments', verbose_name="Сниппет")
    likes = GenericRelation(LikeDislike)

    def __repr__(self):
        return f"C: {self.text[:10]} author:{self.author} sn: {self.snippet.name}"

    @classmethod
    def with_likes_count(cls):
        """QuerySet с предварительно подсчитанными лайками"""
        return cls.objects.annotate(
            likes_count=models.Count('likes',
                                     filter=models.Q(likes__vote=LikeDislike.LIKE)),
            dislikes_count=models.Count('likes',
                                        filter=models.Q(likes__vote=LikeDislike.DISLIKE))
        )

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'Новый комментарий'),
        ('like', 'Новый лайк'),
        ('follow', 'Новый подписчик'),
        ('subscribe_comment', 'Коментарий к сниппету по подписке')
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    snippet = models.ForeignKey(Snippet, on_delete=models.SET_NULL, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Уведомление для {self.recipient.username}: {self.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "snippet")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.snippet.name}"
