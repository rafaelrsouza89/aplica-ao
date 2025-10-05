# aplicacao/management/commands/importar_dados.py
import pandas as pd
from django.core.management.base import BaseCommand
from aplicacao.models import Avaliacao

class Command(BaseCommand):
    help = 'Importa dados de avaliações de livros de um arquivo CSV para o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str, help='O caminho para o arquivo CSV')

    def handle(self, *args, **kwargs):
        caminho_csv = kwargs['caminho_csv']
        
        self.stdout.write(self.style.NOTICE(f'Iniciando a importação do arquivo: {caminho_csv}'))
        
        try:
            df = pd.read_csv(caminho_csv)
            
            
            Avaliacao.objects.all().delete()
            
            avaliacoes_a_criar = []
            for _, row in df.iterrows():
            
                avaliacoes_a_criar.append(Avaliacao(**row.to_dict()))

            
            Avaliacao.objects.bulk_create(avaliacoes_a_criar)
            
            self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Arquivo não encontrado. Verifique o caminho.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro: {e}'))