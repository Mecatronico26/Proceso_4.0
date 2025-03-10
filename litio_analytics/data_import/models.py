# data_import/models.py
import os
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

def get_file_path(instance, filename):
    """Genera una ruta única para cada archivo subido"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class DataFile(models.Model):
    """Modelo para almacenar archivos de datos"""
    name = models.CharField(_("Nombre"), max_length=255)
    description = models.TextField(_("Descripción"), blank=True)
    file = models.FileField(_("Archivo"), upload_to=get_file_path)
    columns = models.JSONField(_("Columnas"), default=dict, blank=True)
    uploaded_at = models.DateTimeField(_("Fecha de subida"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última actualización"), auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Archivo de datos")
        verbose_name_plural = _("Archivos de datos")
        ordering = ['-uploaded_at']

class DataAnalysis(models.Model):
    """Modelo para guardar análisis realizados"""
    name = models.CharField(_("Nombre"), max_length=255)
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name="analyses", verbose_name=_("Archivo de datos"))
    selected_columns = models.JSONField(_("Columnas seleccionadas"))
    chart_type = models.CharField(_("Tipo de gráfico"), max_length=50)
    chart_config = models.JSONField(_("Configuración del gráfico"), default=dict)
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última actualización"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.data_file.name}"
    
    class Meta:
        verbose_name = _("Análisis de datos")
        verbose_name_plural = _("Análisis de datos")
        ordering = ['-created_at']