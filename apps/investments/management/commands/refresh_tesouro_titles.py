from django.core.management.base import BaseCommand

from apps.investments import tesouro


class Command(BaseCommand):
    help = "Baixa o CSV do Tesouro Transparente e sincroniza a tabela TesouroTitulo."

    def handle(self, *args, **options):
        self.stdout.write("Baixando CSV do Tesouro Transparente...")
        criados, atualizados, hist_novo = tesouro.sync_from_csv()
        self.stdout.write(self.style.SUCCESS(
            f"Títulos: {criados} criados, {atualizados} atualizados. "
            f"Histórico: {hist_novo} linhas novas."
        ))
