from django.db import migrations


def update_tesouro_names(apps, schema_editor):
    Investment = apps.get_model("investments", "Investment")
    for inv in Investment.objects.filter(ticker__startswith="TD|"):
        parts = inv.ticker.split("|")
        if len(parts) >= 3:
            tipo = parts[1]
            vencimento = parts[2]
            ano = vencimento.split("-")[0]
            inv.nome = f"{tipo} {ano}"
            inv.save(update_fields=["nome"])


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("investments", "0005_seed_movimentacoes"),
    ]

    operations = [
        migrations.RunPython(update_tesouro_names, reverse),
    ]
