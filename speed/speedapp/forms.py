from django.forms import ModelForm
from django import forms
from .models import *

class TesteForm(ModelForm):

    qtdVoltas = forms.FloatField(required=False)
    tempoTotalMax = forms.FloatField(required=False)

    class Meta:
        model = Teste
        fields = ['id','descricao','qtdVoltas','tipo','tempoTotalMax']
        labels = {
            "tipo": "Finalizar por:",
        }


class AtletaForm(ModelForm):
    class Meta:
        model = Atleta
        fields = ['id','nome','sobreNome','dataNascimento','desporto']
        labels = {
            "nome": "Nome",
            "sobreNome": "Sobrenome",
            "dataNascimento": "Data nascimento",
            "desporto": "Desporto"
        }

class ArestaForm(ModelForm):
    class Meta:
        model = Aresta
        fields = ['id','teste','sensor_a','sensor_b','distancia','descricao']
        labels = {
            "sensor_a": "Sensor (A) *",
            "sensor_b": "Sensor (B) *",
            "distancia": "Distancia (metros) *",
            "descricao": "Descricao (Ex: Saida, Razos, Chegada)"
        }

class AtletaTesteForm(ModelForm):
    testesModelos = forms.ModelChoiceField(queryset=Teste.objects.filter(origem="0"))
    class Meta:
        model = AtletaTeste
        fields = ['id','teste','testesModelos']
        labels = {
            "teste": "Qual teste?"
        }
