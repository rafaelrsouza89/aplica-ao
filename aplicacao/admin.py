from django.contrib import admin
from . models import produtos

class ProdutoAdm(admin.ModelAdmin):
    list_display = ('nome', 'preço', 'qtd')

admin.site.register(produtos, ProdutoAdm)
