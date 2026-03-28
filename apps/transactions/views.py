from django.shortcuts import render
from .forms import TransactionForm

# exibir o formulário para criar uma nova transação
def create_transactions(request):
    form = TransactionForm()
    return render(request, 'transactions/create_transaction.html', {'form': form})

# verificar e enviar os dados do form da transação para o banco de dados (ainda não implementado)
def post_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            transaction_type = form.cleaned_data['transaction_type']
            value = form.cleaned_data['value']
            return render(request, 'transactions/success.html', {'name': name, 'transaction_type': transaction_type, 'value': value})
    else:
        form = TransactionForm()
    return render(request, 'transactions/transactions.html', {'form': form})