from django import forms

# cria um form com as informações para criar uma transação (entrada ou saida)
class TransactionForm(forms.Form):
    name = forms.CharField(max_length=100, label="Nome da transação")
    transaction_type = forms.ChoiceField(choices=[('entrada', 'Entrada'), ('saída', 'Saída')], label="Tipo da transação")
    value = forms.DecimalField(max_digits=10, decimal_places=2, label="Valor")