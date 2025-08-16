from django.conf.urls.static import static
from django.conf import settings
from MainApp import views
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', views.index_page, name="home"),
    path('snippets/add', views.add_snippet_page, name="snippet-add"),
    path('snippets/list', views.snippets_page, {"my_snippets": False}, name="snippets-list"),
    path('snippets/my', views.snippets_page, {"my_snippets": True}, name="snippets-my"),
    path('snippet/<int:id>/delete', views.snippet_delete, name="snippet-delete"),
    path('snippet/<int:id>/edit', views.snippet_edit, name="snippet-edit"),
    path('login', views.login, name="login"),
    path('logout', views.user_logout, name="logout"),
    path('registration', views.user_registration, name="registration"),
    path('comment/add', views.comment_add, name="comment-add"),
    path('notifications/', views.user_notifications, name="notifications"),
    path('snippets/stats', views.snippets_stats_view, name="snippets-stats"),
    path('tags/<int:tag_id>/', views.snippets_by_tag, name="snippets-by-tag"),
    path('snippet/<int:snippet_id>/', views.snippet_detail, name='snippet-detail'),
    path('snippet/<int:snippet_id>/add_tag/', views.add_tag_to_snippet, name='add-tag-to-snippet'),
    path('api/simple-data/', views.simple_api_view, name='simple_api'),
    path('api/notifications/unread-count/', views.unread_notifications_count, name='unread_notifications_count'),
    path('api/is_authenticated', views.is_authenticated, name="unread_notifications_count"),
    path('notifications/delete/', views.notifications_delete, name='delete_read_notifications'),
    path('notifications/delete/<int:id>/', views.notifications_delete, name='delete_notification'),
    path('notifications/mark_read/<int:id>/', views.user_notifications, name='mark_notification'),
    path('api/comment/like/', views.add_comment_like, name="comment-like"),
    path('api/snippet/like/', views.add_snippet_like, name="snippet-like"),

    # path(
    #     'notifications/snippet/<int:snippet_id>/',
    #     views.user_notifications,
    #     name='notifications_by_snippet'
    # ),
    path('profile/', views.user_profile, name="profile"),
]
# if settings.DEBUG:
#     import debug_toolbar
#     # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += path('__debug__/', include(debug_toolbar.urls))

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
