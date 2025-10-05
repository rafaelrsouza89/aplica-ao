from django.urls import path
from . import views

urlpatterns = [
    path('' , views.index, name="url_index"),
    path('produto', views.produto, name="url_produto"),
    path('lista_vendas', views.lista_vendas, name="url_lista_vendas"),
    path('cad_produto', views.cad_produto, name="url_cad_produto"),
    path('atualizar_produto/<int:id>', views.atualizar_produto, name="url_atualizar_produto"),
    path('apagar_produto/<int:id>', views.apagar_produto, name="url_apagar_produto"),
    path('entrar', views.entrar, name="url_entrar"),
    path('cad_user', views.cad_user, name="url_cad_user"),
    path('cad_cliente', views.cad_cliente, name="url_cad_cliente"),
    path('registrar_venda', views.registrar_venda, name="url_registrar_venda"),
    path('sair', views.sair, name="url_sair"),
    path('analise/', views.dashboard_completo_view, name='dashboard_completo'),
    path('analise/usuarios-ativos/', views.usuarios_mais_ativos_view, name='analise_usuarios_ativos'),
    path('analise/evolucao-reviews/', views.evolucao_reviews_view, name='analise_evolucao_reviews'),
    path('analise/preco-vs-score/', views.preco_vs_score_view, name='analise_preco_score'),
    path('analise/sentimento-reviews/', views.sentimento_reviews_view, name='analise_sentimento'),
]