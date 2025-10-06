from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from aplicacao.templates.forms import ClienteForm, PerfilForm
from .models import Produto, Cliente, Venda, ItemVenda
from django.http.response import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import io
import pandas as pd
import matplotlib.pyplot as plt
from .models import Avaliacao 
import urllib, base64
from django.shortcuts import render


def index(request):
    return redirect('url_entrar')

@login_required(login_url="url_entrar")
def produto(request):
    produtos = Produto.objects.all()
    context = {
        'produtos': produtos,
    }
    return render(request, 'produto.html', context)

@login_required(login_url="url_entrar")
def cad_produto(request):
    if request.method == "POST":
        nome = request.POST.get('nome')
        preco = request.POST.get('preco', '0').replace(',', '.')
        qtde = request.POST.get('qtde', '0')
        Produto.objects.create(nome=nome, preco=Decimal(preco), qtde=int(qtde))
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('url_produto')
    return render(request, 'cad_produto.html')

@login_required(login_url="url_entrar")
def atualizar_produto(request, id):
    prod = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        prod.nome = request.POST.get('nome')
        prod.preco = Decimal(request.POST.get('preco', '0').replace(',', '.'))
        prod.qtde = int(request.POST.get('qtde', '0'))
        prod.save()
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('url_produto')
    context = {'prod': prod}
    return render(request, 'atualizar_produto.html', context)

@login_required(login_url="url_entrar")
def apagar_produto(request, id):
    prod = get_object_or_404(Produto, id=id)
    prod.delete()
    messages.success(request, 'Produto apagado com sucesso!')
    return redirect('url_produto')

def entrar(request):
    if request.method == "POST":
        username = request.POST.get('nome')
        password = request.POST.get('senha')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('url_produto')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, "entrar.html")

def cad_user(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        senha = request.POST.get('senha')
        email = request.POST.get('email')
        if User.objects.filter(username=nome).exists():
            messages.error(request, 'Este nome de usuário já existe.')
        else:
            User.objects.create_user(username=nome, email=email, password=senha)
            messages.success(request, 'Usuário cadastrado com sucesso! Faça o login.')
            return redirect('url_entrar')
    return render(request, "cad_user.html")
    
def sair(request):
    logout(request)
    return redirect('url_entrar')

@login_required(login_url="url_entrar")
def cad_cliente(request):
    if request.method == "POST":
        form_cliente = ClienteForm(request.POST)
        form_perfil = PerfilForm(request.POST)
        if form_cliente.is_valid() and form_perfil.is_valid():
            cliente = form_cliente.save()
            perfil = form_perfil.save(commit=False)
            perfil.cliente = cliente
            perfil.save()
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('url_produto')
    else:
        form_cliente = ClienteForm()
        form_perfil = PerfilForm()
    context = {
        'form_cliente': form_cliente,
        'form_perfil': form_perfil
    }
    return render(request, "cad_cliente.html", context)

@login_required(login_url="url_entrar")
def registrar_venda(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        if not cliente_id:
            messages.error(request, 'Você precisa selecionar um cliente.')
            return redirect('url_registrar_venda')

        cliente = get_object_or_404(Cliente, id=cliente_id)

        with transaction.atomic():
            nova_venda = Venda.objects.create(cliente=cliente)
            valor_total_venda = Decimal('0.0')
            pelo_menos_um_produto = False

            for produto in Produto.objects.all():
                quantidade_str = request.POST.get(f'produto_{produto.id}')
                if quantidade_str and int(quantidade_str) > 0:
                    pelo_menos_um_produto = True
                    quantidade = int(quantidade_str)

                    if quantidade > produto.qtde:
                        messages.error(request, f"Erro! Estoque insuficiente para o produto '{produto.nome}'.")
                        transaction.set_rollback(True)
                        return redirect('url_registrar_venda')

                    ItemVenda.objects.create(
                        venda=nova_venda,
                        produto=produto,
                        quantidade=quantidade,
                        preco_unitario=produto.preco
                    )
                    
                    produto.qtde -= quantidade
                    produto.save() 
                    valor_total_venda += produto.preco * quantidade
            
            if not pelo_menos_um_produto:
                messages.error(request, 'A venda precisa ter pelo menos um produto.')
                transaction.set_rollback(True)
                return redirect('url_registrar_venda')
         
            nova_venda.valor_total = valor_total_venda
            nova_venda.save()
            
            messages.success(request, 'Venda registrada com sucesso!')
            return redirect('url_produto')

    else: 
        clientes = Cliente.objects.all()
        produtos = Produto.objects.all()
        context = {
            'clientes': clientes,
            'produtos': produtos,
        }
        return render(request, 'registrar_venda.html', context)

@login_required(login_url="url_entrar")
def lista_vendas(request):
    vendas = Venda.objects.all().order_by('-data_venda')

    # Gera os gráficos das análises
    df = get_dataframe()

    # Gráfico 1: Top 15 Usuários Mais Ativos
    grafico_usuarios_ativos = None
    if not df.empty and 'profile_name' in df.columns:
        top_15_usuarios = df.dropna(subset=['profile_name'])['profile_name'].value_counts().nlargest(15)
        plt.figure(figsize=(12, 8))
        top_15_usuarios.sort_values().plot(kind='barh', color='skyblue')
        plt.title('Top 15 Usuários Mais Ativos')
        plt.xlabel('Número de Avaliações')
        plt.ylabel('Usuário')
        plt.tight_layout()
        grafico_usuarios_ativos = plot_to_base64(plt.gcf())
        plt.close()

    # Gráfico 2: Evolução das Avaliações por Ano
    grafico_evolucao_reviews = None
    if not df.empty and 'review_time' in df.columns:
        df['data_review'] = pd.to_datetime(df['review_time'], unit='s')
        df['ano'] = df['data_review'].dt.year
        reviews_por_ano = df['ano'].value_counts().sort_index()
        plt.figure(figsize=(10, 6))
        reviews_por_ano.plot(kind='line', marker='o', color='green')
        plt.title('Evolução do Número de Avaliações por Ano')
        plt.xlabel('Ano')
        plt.ylabel('Quantidade de Avaliações')
        plt.grid(True, linestyle='--')
        plt.tight_layout()
        grafico_evolucao_reviews = plot_to_base64(plt.gcf())
        plt.close()

    # Gráfico 3: Preço vs Score
    grafico_preco_score = None
    if not df.empty and 'price' in df.columns and 'review_score' in df.columns:
        df_filtered = df[(df['price'] > 0) & (df['price'] < 100)]
        if not df_filtered.empty:
            df_sample = df_filtered.sample(n=min(1000, len(df_filtered)), random_state=42)
            plt.figure(figsize=(10, 6))
            plt.scatter(df_sample['price'], df_sample['review_score'], alpha=0.3)
            plt.title('Correlação entre Preço e Nota da Avaliação (Amostra)')
            plt.xlabel('Preço (Price)')
            plt.ylabel('Nota (Score)')
            plt.grid(True, linestyle='--')
            plt.tight_layout()
            grafico_preco_score = plot_to_base64(plt.gcf())
            plt.close()

    # Gráfico 4: Sentimento dos Sumários
    grafico_sentimento = None
    if not df.empty and 'review_summary' in df.columns:
        palavras_positivas = ['good', 'great', 'excellent', 'love', 'amazing', 'best', 'recommend']
        palavras_negativas = ['bad', 'terrible', 'disappointing', 'not good', 'waste', 'awful']
        def classificar_sentimento(texto):
            if any(palavra in texto for palavra in palavras_positivas): return 'Positivo'
            if any(palavra in texto for palavra in palavras_negativas): return 'Negativo'
            return 'Neutro'
        df['sentimento'] = df['review_summary'].fillna('').str.lower().apply(classificar_sentimento)
        contagem_sentimentos = df['sentimento'].value_counts()
        plt.figure(figsize=(8, 8))
        contagem_sentimentos.plot(kind='pie', autopct='%1.1f%%', colors=['lightgreen', 'lightcoral', 'lightskyblue'])
        plt.title('Distribuição de Sentimentos nos Sumários das Avaliações')
        plt.ylabel('')
        grafico_sentimento = plot_to_base64(plt.gcf())
        plt.close()

    context = {
        'vendas': vendas,
        'grafico_usuarios_ativos': grafico_usuarios_ativos,
        'grafico_evolucao_reviews': grafico_evolucao_reviews,
        'grafico_preco_score': grafico_preco_score,
        'grafico_sentimento': grafico_sentimento,
    }
    return render(request, 'lista_vendas.html', context)

def get_dataframe():
    avaliacoes = Avaliacao.objects.all().values()
    df = pd.DataFrame(list(avaliacoes))
    return df
def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    return urllib.parse.quote(string)
def usuarios_mais_ativos(df):
    usuarios_ativos = df.dropna(subset=['profile_name'])['profile_name'].value_counts().nlargest(15)
    plt.figure(figsize=(12, 8))
    usuarios_ativos.sort_values().plot(kind='barh', color='blue')
    plt.title('Top 15 Usuários Mais Ativos"')
    plt.xlabel('Número de Avaliações')
    plt.ylabel('Usuário')
    plt.tight_layout() 
    plt.show()
def evolucacao_ao_longo_do_tempo():
    df = get_dataframe()
    df['data_review'] = pd.to_datetime(df['review_time'], unit='s')
    df['ano'] = df['data_review'].dt.year
   
   
def preco_vs_notas():

    def get_dataframe():
        avaliacoes = Avaliacao.objects.all().values()
        df = pd.DataFrame(list(avaliacoes))
        return df

def plot_to_base64(fig):
    """Converte uma figura Matplotlib para uma string base64 para ser usada no HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    return urllib.parse.quote(string)

# --- Views de Análise ---

def usuarios_mais_ativos_view(request):
    """ANÁLISE 1: Identifica e visualiza os 15 usuários que mais publicaram avaliações."""
    df = get_dataframe()
    df_filtered = df.dropna(subset=['profile_name'])
    top_15_usuarios = df_filtered['profile_name'].value_counts().nlargest(15)
    
    plt.figure(figsize=(12, 8))
    top_15_usuarios.sort_values().plot(kind='barh', color='skyblue')
    plt.title('Top 15 Usuários Mais Ativos')
    plt.xlabel('Número de Avaliações')
    plt.ylabel('Usuário')
    plt.tight_layout()
    
    grafico = plot_to_base64(plt.gcf())
    plt.close()
    
    context = {'grafico_usuarios_ativos': grafico}
    return render(request, 'aplicacao/dashboard_analise.html', context)

def evolucao_reviews_view(request):
    """ANÁLISE 2: Visualiza a quantidade de avaliações de livros por ano."""
    df = get_dataframe()
    df['data_review'] = pd.to_datetime(df['review_time'], unit='s')
    df['ano'] = df['data_review'].dt.year
    reviews_por_ano = df['ano'].value_counts().sort_index()
    
    plt.figure(figsize=(10, 6))
    reviews_por_ano.plot(kind='line', marker='o', color='green')
    plt.title('Evolução do Número de Avaliações por Ano')
    plt.xlabel('Ano')
    plt.ylabel('Quantidade de Avaliações')
    plt.grid(True, linestyle='--')
    plt.tight_layout()
    
    grafico = plot_to_base64(plt.gcf())
    plt.close()
    
    context = {'grafico_evolucao_reviews': grafico}
    return render(request, 'aplicacao/dashboard_analise.html', context)

def preco_vs_score_view(request):
    """ANÁLISE 3: Investiga a correlação entre o preço do livro e a nota da avaliação."""
    df = get_dataframe()
    df_filtered = df[(df['price'] > 0) & (df['price'] < 100)]
    df_sample = df_filtered.sample(n=min(1000, len(df_filtered)), random_state=42)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(df_sample['price'], df_sample['review_score'], alpha=0.3)
    plt.title('Correlação entre Preço e Nota da Avaliação (Amostra)')
    plt.xlabel('Preço (Price)')
    plt.ylabel('Nota (Score)')
    plt.grid(True, linestyle='--')
    plt.tight_layout()
    
    grafico = plot_to_base64(plt.gcf())
    plt.close()
    
    context = {'grafico_preco_score': grafico}
    return render(request, 'aplicacao/dashboard_analise.html', context)

def sentimento_reviews_view(request):
    """ANÁLISE 4: Realiza uma análise de sentimento básica sobre os sumários das avaliações."""
    df = get_dataframe()
    palavras_positivas = ['good', 'great', 'excellent', 'love', 'amazing', 'best', 'recommend']
    palavras_negativas = ['bad', 'terrible', 'disappointing', 'not good', 'waste', 'awful']

    def classificar_sentimento(texto):
        if any(palavra in texto for palavra in palavras_positivas): return 'Positivo'
        if any(palavra in texto for palavra in palavras_negativas): return 'Negativo'
        return 'Neutro'

    df['sentimento'] = df['review_summary'].fillna('').str.lower().apply(classificar_sentimento)
    contagem_sentimentos = df['sentimento'].value_counts()
    
    plt.figure(figsize=(8, 8))
    contagem_sentimentos.plot(kind='pie', autopct='%1.1f%%', colors=['lightgreen', 'lightcoral', 'lightskyblue'])
    plt.title('Distribuição de Sentimentos nos Sumários das Avaliações')
    plt.ylabel('')
    
    grafico = plot_to_base64(plt.gcf())
    plt.close()
    
    context = {'grafico_sentimento': grafico}
    return render(request, 'aplicacao/dashboard_analise.html', context)
    
def dashboard_completo_view(request):
    """View que reúne todos os gráficos em uma única página."""
    # Como gerar cada gráfico e adicioná-lo ao contexto levaria tempo,
    # esta view pode servir como um exemplo de como combinar contextos.
    # Por ora, vamos criar links para cada análise separada.
    context = {}
    return render(request, 'aplicacao/dashboard_completo.html', context)
    
    
    pass