from django.shortcuts import render
from.models import produtos 
def index(request):
    context = {
        'texto' : "Olá mundo!",
    }
    return render(request, 'index.html', context)

def produtos(request):
    produtos = produtos.objects.all()
    context = {
        'produtos': produtos 
    
return render(request, 'index.html', context)
    }