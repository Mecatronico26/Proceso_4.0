# data_visualization/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from data_import.models import DataAnalysis

class ScheduledReport(models.Model):
    """Modelo para programar informes automáticos"""
    
    FREQUENCY_CHOICES = (
        ('daily', _('Diario')),
        ('weekly', _('Semanal')),
        ('biweekly', _('Quincenal')),
        ('monthly', _('Mensual')),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('png', 'Imagen PNG'),
    )
    
    name = models.CharField(_("Nombre"), max_length=255)
    description = models.TextField(_("Descripción"), blank=True)
    analysis = models.ForeignKey(DataAnalysis, on_delete=models.CASCADE, related_name="scheduled_reports", verbose_name=_("Análisis"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scheduled_reports", verbose_name=_("Usuario"))
    frequency = models.CharField(_("Frecuencia"), max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    day_of_week = models.PositiveSmallIntegerField(_("Día de la semana"), null=True, blank=True, help_text=_("1-7, donde 1 es lunes (solo para frecuencia semanal o quincenal)"))
    day_of_month = models.PositiveSmallIntegerField(_("Día del mes"), null=True, blank=True, help_text=_("1-31 (solo para frecuencia mensual)"))
    time = models.TimeField(_("Hora de envío"))
    recipients = models.TextField(_("Destinatarios"), help_text=_("Correos electrónicos separados por comas"))
    subject = models.CharField(_("Asunto"), max_length=255)
    message = models.TextField(_("Mensaje"), help_text=_("Mensaje personalizado para el correo"))
    include_data = models.BooleanField(_("Incluir datos"), default=True, help_text=_("Adjuntar datos en el formato seleccionado"))
    format = models.CharField(_("Formato"), max_length=10, choices=FORMAT_CHOICES, default='pdf')
    is_active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última actualización"), auto_now=True)
    last_sent = models.DateTimeField(_("Último envío"), null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    class Meta:
        verbose_name = _("Informe programado")
        verbose_name_plural = _("Informes programados")
        ordering = ['-created_at']


class ReportLog(models.Model):
    """Modelo para registrar el envío de informes"""
    
    STATUS_CHOICES = (
        ('success', _('Éxito')),
        ('failed', _('Fallido')),
    )
    
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE, related_name="logs", verbose_name=_("Informe programado"))
    sent_at = models.DateTimeField(_("Fecha de envío"), auto_now_add=True)
    status = models.CharField(_("Estado"), max_length=10, choices=STATUS_CHOICES)
    recipients = models.TextField(_("Destinatarios"))
    error_message = models.TextField(_("Mensaje de error"), blank=True, null=True)
    
    def __str__(self):
        return f"{self.scheduled_report.name} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = _("Registro de envío")
        verbose_name_plural = _("Registros de envío")
        ordering = ['-sent_at']