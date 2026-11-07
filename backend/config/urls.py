
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static



from core.views import (
    inicio,
    login_view,
    dashboard,
    produtos,
    novo_produto,
    editar_produto,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('produtos/', produtos, name='produtos'),
    path('produtos/novo/', novo_produto, name='novo_produto'),
    path(
        'produtos/editar/<int:produto_id>/',
        editar_produto,
        name='editar_produto'
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

