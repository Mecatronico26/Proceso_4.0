# data_visualization/forms.py
from django import forms
from .models import ScheduledReport
import re

class ScheduledReportForm(forms.ModelForm):
    """Formulario para crear y editar informes programados"""
    
    class Meta:
        model = ScheduledReport
        fields = [
            'name', 'description', 'frequency', 'day_of_week', 'day_of_month', 'time',
            'recipients', 'subject', 'message', 'include_data', 'format', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'message': forms.Textarea(attrs={'rows': 4}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales dependiendo de la frecuencia seleccionada
        self.fields['day_of_week'].required = False
        self.fields['day_of_month'].required = False
    
    def clean_recipients(self):
        """Validar que los correos electrónicos estén en formato correcto"""
        recipients = self.cleaned_data.get('recipients', '')
        emails = [email.strip() for email in recipients.split(',') if email.strip()]
        
        if not emails:
            raise forms.ValidationError("Debe especificar al menos un destinatario.")
        
        # Validar formato de correo electrónico
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        invalid_emails = []
        
        for email in emails:
            if not email_pattern.match(email):
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                f"Los siguientes correos no tienen un formato válido: {', '.join(invalid_emails)}"
            )
        
        return recipients
    
    def clean(self):
        """Validar campos según la frecuencia seleccionada"""
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        day_of_week = cleaned_data.get('day_of_week')
        day_of_month = cleaned_data.get('day_of_month')
        
        if frequency in ['weekly', 'biweekly']:
            if not day_of_week:
                self.add_error('day_of_week', "Este campo es requerido para la frecuencia seleccionada.")
            elif day_of_week < 1 or day_of_week > 7:
                self.add_error('day_of_week', "El día de la semana debe estar entre 1 (lunes) y 7 (domingo).")
        
        if frequency == 'monthly':
            if not day_of_month:
                self.add_error('day_of_month', "Este campo es requerido para la frecuencia mensual.")
            elif day_of_month < 1 or day_of_month > 31:
                self.add_error('day_of_month', "El día del mes debe estar entre 1 y 31.")
        
        return cleaned_data