from django.core.management.base import BaseCommand
from aplicacao.models import Avaliacao
import csv

class Command(BaseCommand):
    help = 'Importa dados de avaliações de livros de um arquivo CSV para o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str, help='O caminho para o arquivo CSV')

    def handle(self, *args, **kwargs):
        caminho_csv = kwargs['caminho_csv']
        with open(caminho_csv, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            Avaliacao.objects.all().delete()
            for row in reader:
                Avaliacao.objects.create(
                    id_evaluation=row.get('id_evaluation'),
                    title=row.get('title'),
                    price=row.get('price') or None,
                    user_id=row.get('user_id'),
                    profile_name=row.get('profile_name'),
                    review_helpfulness=row.get('review_helpfulness'),
                    review_score=row.get('review_score'),
                    review_time=row.get('review_time'),
                    review_summary=row.get('review_summary'),
                    review_text=row.get('review_text'),
                )
        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))