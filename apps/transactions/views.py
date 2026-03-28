from django.shortcuts import render
from .forms import TransactionForm
from .models import Transaction
from django.db.models import Sum, Q

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

# EXIBIR o extrato (entradas e saída) + o saldo 
def get_transactions(request):
    transactions = Transaction.objects.all().order_by('-date')
    # Cálculo do saldo total
    totais = transactions.aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')), 
        #soma das entrada 
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL')) 
    )  
    total_entradas = totais['e'] or 0
    total_saidas = totais['s'] or 0
    saldo = total_entradas - total_saidas
    #saldo = (totais['e'] or 0) - (totais['s'] or 0)
    return render(request, 'transactions/list_transactions.html', {
        'transactions': transactions, 
        'total_entradas': total_entradas, 
        'total_saidas': total_saidas,     
        'saldo': saldo                    
    })