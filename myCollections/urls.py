from django.urls import path
from .views import RegisterUserView, MoviesListView, CollectionListView, CollectionListDetailView, RequestCountView, \
    UserCreateView, UserDeleteView, UserListView

urlpatterns = [
    path('create-user/', UserCreateView.as_view(), name='user-create'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('delete/user/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('movies/', MoviesListView.as_view(), name='movies'),
    path('collection/', CollectionListView.as_view(), name='collection'),
    path('collection/<slug:collection_uuid>', CollectionListDetailView.as_view(), name='detail-collection'),
    path('request-count/', RequestCountView.as_view(), name='request-count'),
    path('request-count/reset/', RequestCountView.as_view(), name='request-count-reset'),
]