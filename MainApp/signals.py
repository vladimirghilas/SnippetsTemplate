from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User
from django.db.models import F

from MainApp.models import Snippet, Comment, Notification, Subscription

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
        preview_text = instance.text
        if len(preview_text) > 100:
            preview_text = preview_text[:100] + "..."

        Notification.objects.create(
            recipient=instance.snippet.user,
            notification_type="comment",
            title=f'Новый комментарий к спиппету {instance.snippet.name}',
            comment=instance,
            message=f'Пользователь {instance.author.username} оставил комментарий к вашему сниппету: {preview_text}'
        )

@receiver(post_save, sender=Comment)
def notify_subscribers_on_comment(sender, instance, created, **kwargs):
    """
    Создает уведомления для всех подписчиков на сниппет, на который оставлен комментарий,
    за исключением автора комментария и, если нужно, автора сниппета.
    """
    if created:
        snippet = instance.snippet
        # Все подписчики на сниппет, кроме автора комментария
        subscribers = Subscription.objects.filter(snippet=snippet).exclude(user=instance.author)

        preview_text = instance.text
        if len(preview_text) > 100:
            preview_text = preview_text[:100] + "..."  # ограничение длины текста уведомления

        for sub in subscribers:
            Notification.objects.create(
                recipient=sub.user,
                notification_type="subscribe_comment",
                title=f"Новый комментарий к сниппету на который вы подписаны{snippet.name}",
                comment=instance,
                snippet=snippet,
                message=f"Пользователь {instance.author.username} оставил комментарий: {preview_text}"
            )

@receiver(post_save, sender=Snippet)
def notify_subscribers_on_snippet_update(sender, instance, created, **kwargs):
    if created:
        return  # ничего не делаем при создании

    # Получаем всех подписчиков, кроме автора
    subscribers = Subscription.objects.filter(snippet=instance).exclude(user=instance.user)

    notifications = [
        Notification(
            recipient=sub.user,
            notification_type="snippet_update",
            title=f'Обновление сниппета "{instance.name}"',
            snippet=instance,
            message=f'Автор {instance.user.username} обновил сниппет: {instance.name}'
        )
        for sub in subscribers
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)
