from django.contrib import admin
from MainApp.models import Snippet, Comment, Tag, Notification
from django.db.models import Count

class SnippetAdmin(admin.ModelAdmin):
    list_display = ('name', 'lang', 'user', 'num_comments')
    list_filter = ('lang', 'public')
    search_fields = ('name', )
    fields = ('name', 'lang', 'code', 'public', 'user')
    # Метод для получения queryset с аннотированным полем
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Аннотируем каждую запись количеством комментариев
        queryset = queryset.annotate(
            num_comments=Count('comments', distinct=True)
        )
        return queryset

    # Добавление пользовательского поля
    def num_comments(self, obj):
        return obj.num_comments

    # Определение заголовка для пользовательского поля
    num_comments.short_description = 'Кол-во комментариев'

class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'snippet')
    list_filter = ('author',)
    search_fields = ('creation_date',)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'snippet_count')
    list_filter = ('name',)
    search_fields = ('name',)

    def snippet_count(self, obj):
        return obj.snippet_set.count
    snippet_count.short_description = "Кол-во сниппетов"

#@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    readonly_fields = ['created_at']

    # Register your models here.

admin.site.register(Snippet, SnippetAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.site_header = 'Snippets Admin'
admin.site.site_title = 'Snippets Admin Portal'
admin.site.index_title = 'Wellcome to Snippets Admin Portal'
