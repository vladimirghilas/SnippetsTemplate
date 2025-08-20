from django.conf.urls.static import static
from django.conf import settings
from MainApp import views, views_cbv
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from MainApp import views as main_views
from MainApp.views_cbv import LogoutView, UserNotificationsView

urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', views.index_page, name="home"),
    # path('snippets/add', views.add_snippet_page, name="snippet-add"),
    path('snippets/add', views_cbv.AddSnippetView.as_view(), name="snippet-add"),
    path('snippets/list', views.snippets_page, {"my_snippets": False}, name="snippets-list"),
    path('snippets/my', views.snippets_page, {"my_snippets": True}, name="snippets-my"),
    path('snippet/<int:id>/delete', views.snippet_delete, name="snippet-delete"),
    path('snippet/<int:id>/edit', views.snippet_edit, name="snippet-edit"),
    path('login/', views.login, name="login"),
    # path('logout', views.user_logout, name="logout"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('registration', views.user_registration, name="registration"),
    path('comment/add', views.comment_add, name="comment-add"),
    path('snippets/stats', views.snippets_stats_view, name="snippets-stats"),
    path('tags/<int:tag_id>/', views.snippets_by_tag, name="snippets-by-tag"),
    # path('snippet/<int:snippet_id>/', views.snippet_detail, name='snippet-detail'),
    path('snippet/<int:pk>/', views_cbv.SnippetDetailView.as_view(), name='snippet-detail'),
    path('snippet/<int:snippet_id>/add_tag/', views.add_tag_to_snippet, name='add-tag-to-snippet'),
    path('api/simple-data/', views.simple_api_view, name='simple_api'),
    # path('notifications/', views.user_notifications, name="notifications"),
    path("notifications/", UserNotificationsView.as_view(), name="user_notifications"),
    path('api/notifications/unread-count/', views.unread_notifications_count, name='unread_notifications_count'),
    path('api/is_authenticated', views.is_authenticated, name="unread_notifications_count"),
    path('notifications/delete/', views.notifications_delete, name='delete_read_notifications'),
    path('notifications/delete/<int:id>/', views.notifications_delete, name='delete_notification'),
    path('notifications/mark_read/<int:id>/', views.user_notifications, name='mark_notification'),
    path('activate/<int:user_id>/<str:token>/', views.activate_account, name='activate_account'),
    path('resend_email/', views.resend_email, name='resend_email'),
    path('delete-account/', views.delete_account_view, name='delete_account'),

    path('api/comment/like/', views.add_comment_like, name="comment-like"),
    path('api/snippet/like/', views.add_snippet_like, name="snippet-like"),

    # path(
    #     'notifications/snippet/<int:snippet_id>/',
    #     views.user_notifications,
    #     name='notifications_by_snippet'
    # ),
    path('profile/', views.my_profile, name='profile'),  # profilul curent
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    # Смена пароля для авторизованного пользователя
    path('password/change/',
         auth_views.PasswordChangeView.as_view(template_name='pages/password_change.html'),
         name='password_change'),
    path('password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='pages/password_change_done.html'),
         name='password_change_done'),

]
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
