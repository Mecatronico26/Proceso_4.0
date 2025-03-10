# data_import/forms.py
from django import forms
from .models import DataFile, DataAnalysis

class DataFileForm(forms.ModelForm):
    """Formulario para subir archivos de datos"""
    class Meta:
        model = DataFile
        fields = ['name', 'description', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ColumnSelectionForm(forms.Form):
    """Formulario dinámico para seleccionar columnas a analizar"""
    def __init__(self, columns, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for column in columns:
            self.fields[f'column_{column}'] = forms.BooleanField(
                label=column,
                required=False,
                initial=True,
            )
        
        self.fields['chart_type'] = forms.ChoiceField(
            label="Tipo de gráfico",
            choices=[
                ('line', 'Línea'),
                ('bar', 'Barras'),
                ('scatter', 'Dispersión'),
                ('pie', 'Pastel'),
                ('histogram', 'Histograma'),
                ('box', 'Caja y bigotes'),
                ('heatmap', 'Mapa de calor'),
            ],
            initial='line',
        )
        
        self.fields['x_axis'] = forms.ChoiceField(
            label="Eje X",
            choices=[('', '-- Seleccionar --')] + [(col, col) for col in columns],
            required=False,
        )