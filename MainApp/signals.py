from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User
from django.db.models import F

from MainApp.models import Snippet, Comment, Notification

# signals
snippet_view = Signal()


@receiver(post_save, sender=User)
def send_message(sender, instance, created, **kwargs):
    if created:
        print(f'User {instance.username} was created')

@receiver(snippet_view, sender=None)
def add_view_count(sender, snippet, **kwargs):
    snippet.views_count = F('views_count') + 1
    snippet.save(update_fields=['views_count'])
    snippet.refresh_from_db()

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.snippet.user and instance.author != instance.snippet.user:
        Notification.objects.create(
            recipient = instance.snippet.user,
            notification_type="comment",
            title='Новый комментарий',
            message=f'{instance.author.username} оставил комментарий к вашему сниппету:{instance.snippet.name}'
        )