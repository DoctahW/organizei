from django.db import migrations


def backfill_taxa_na_data(apps, schema_editor):
    """Preenche taxa_na_data das compras de Tesouro já existentes.

    Sem essa taxa a marcação na curva não tem rendimento. Como não há
    histórico de taxa para datas passadas, usamos a taxa atual do título
    como melhor aproximação disponível.
    """
    Investment = apps.get_model("investments", "Investment")
    TesouroTitulo = apps.get_model("investments", "TesouroTitulo")

    for inv in Investment.objects.filter(tipo="tesouro"):
        parts = (inv.ticker or "").split("|", 2)
        if len(parts) != 3 or parts[0] != "TD":
            continue
        tipo, vencimento_iso = parts[1], parts[2]
        titulo = TesouroTitulo.objects.filter(
            tipo=tipo, vencimento=vencimento_iso
        ).first()
        if titulo is None:
            continue
        inv.movimentacoes.filter(tipo="compra", taxa_na_data__isnull=True).update(
            taxa_na_data=titulo.taxa_compra
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("investments", "0007_investmentmovimentacao_taxa_na_data_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_taxa_na_data, noop),
    ]
