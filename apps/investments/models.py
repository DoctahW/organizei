from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce


class Investment(models.Model):
    TYPE_CHOICES = [
        ("acao", "Ação"),
        ("fii", "Fundo Imobiliário"),
        ("tesouro", "Tesouro Direto"),
        ("renda_fixa", "Renda Fixa"),
        ("fundo", "Fundo de Investimento"),
        ("cripto", "Criptomoeda"),
        ("outro", "Outro"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments")
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TYPE_CHOICES)
    ticker = models.CharField(max_length=100, blank=True)
    pu_atual = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    cotacao_atualizada_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Campos cacheados a partir das movimentações; atualizados por recalc().
    quantidade = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    valor_aplicado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    valor_atual = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    data_aplicacao = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.nome

    def recalc(self):
        """Recalcula campos cacheados a partir das movimentações."""
        agg = self.movimentacoes.aggregate(
            qtd_compra=Coalesce(Sum("quantidade", filter=Q(tipo="compra")), Value(Decimal("0"))),
            qtd_venda=Coalesce(Sum("quantidade", filter=Q(tipo="venda")), Value(Decimal("0"))),
            val_compra=Coalesce(Sum("valor", filter=Q(tipo="compra")), Value(Decimal("0"))),
            val_venda=Coalesce(Sum("valor", filter=Q(tipo="venda")), Value(Decimal("0"))),
        )
        self.quantidade = agg["qtd_compra"] - agg["qtd_venda"]
        self.valor_aplicado = agg["val_compra"] - agg["val_venda"]
        if self.pu_atual is not None:
            self.valor_atual = (self.quantidade * self.pu_atual).quantize(Decimal("0.01"))
        else:
            self.valor_atual = self.valor_aplicado
        primeira = self.movimentacoes.filter(tipo="compra").order_by("data").values_list("data", flat=True).first()
        if primeira:
            self.data_aplicacao = primeira
        self.save(update_fields=["quantidade", "valor_aplicado", "valor_atual", "data_aplicacao"])

    @property
    def rendimento(self):
        return self.valor_atual - self.valor_aplicado

    @property
    def rentabilidade_pct(self):
        if self.valor_aplicado <= 0:
            return Decimal("0.00")
        return ((self.rendimento / self.valor_aplicado) * Decimal("100")).quantize(Decimal("0.01"))

    @property
    def preco_medio(self):
        agg = self.movimentacoes.filter(tipo="compra").aggregate(
            qtd=Coalesce(Sum("quantidade"), Value(Decimal("0"))),
            val=Coalesce(Sum("valor"), Value(Decimal("0"))),
        )
        if agg["qtd"] <= 0:
            return None
        return (agg["val"] / agg["qtd"]).quantize(Decimal("0.0001"))


class TesouroTitulo(models.Model):
    tipo = models.CharField(max_length=100)
    vencimento = models.DateField()
    data_base = models.DateField()
    pu_compra = models.DecimalField(max_digits=14, decimal_places=4)
    pu_venda = models.DecimalField(max_digits=14, decimal_places=4)
    taxa_compra = models.DecimalField(max_digits=8, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tipo", "vencimento")]
        ordering = ["tipo", "vencimento"]

    def __str__(self):
        return f"{self.tipo} {self.vencimento.isoformat()}"


class TesouroPrecoHistorico(models.Model):
    tipo = models.CharField(max_length=100)
    vencimento = models.DateField()
    data = models.DateField()
    pu_compra = models.DecimalField(max_digits=14, decimal_places=4)
    pu_venda = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        unique_together = [("tipo", "vencimento", "data")]
        indexes = [models.Index(fields=["tipo", "vencimento", "data"])]


class InvestmentMovimentacao(models.Model):
    TIPO_CHOICES = [
        ("compra", "Compra / Aporte"),
        ("venda", "Resgate / Venda"),
    ]

    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name="movimentacoes")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    data = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    quantidade = models.DecimalField(max_digits=14, decimal_places=4)
    pu_na_data = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    observacao = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-created_at"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.investment.nome} {self.data.isoformat()}"
