from django.db import migrations


def create_subscription_category(apps, schema_editor):
    Category = apps.get_model('transactions', 'Category')
    Category.objects.get_or_create(name='Assinatura', user=None)


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0007_transaction_subscription'),
    ]

    operations = [
        migrations.RunPython(create_subscription_category, migrations.RunPython.noop),
    ]