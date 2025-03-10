# data_import/views.py
import os
import json
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.conf import settings

from .models import DataFile, DataAnalysis
from .forms import DataFileForm, ColumnSelectionForm
from .utils import read_excel_file, get_column_statistics, convert_df_to_json

class DataFileUploadView(CreateView):
    """Vista para subir un nuevo archivo de datos"""
    model = DataFile
    form_class = DataFileForm
    template_name = 'data_import/upload.html'
    
    def form_valid(self, form):
        # Guardar el archivo
        self.object = form.save()
        
        # Procesar el archivo para obtener información de las columnas
        try:
            file_path = self.object.file.path
            df, info = read_excel_file(file_path)
            
            # Guardar información de las columnas en el modelo
            self.object.columns = {
                'list': info['columns'],
                'info': get_column_statistics(df),
                'rows': info['rows'],
                'sheet_name': info['sheet_name'],
                'sheets_available': info['sheets_available'],
            }
            self.object.save()
            
            messages.success(self.request, f'Archivo "{self.object.name}" subido correctamente. Se encontraron {len(info["columns"])} columnas y {info["rows"]} filas.')
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo: {str(e)}')
        
        return redirect('data_file_detail', pk=self.object.pk)

class DataFileListView(ListView):
    """Vista para mostrar la lista de archivos subidos"""
    model = DataFile
    template_name = 'data_import/list.html'
    context_object_name = 'data_files'
    ordering = ['-uploaded_at']
    paginate_by = 10

class DataFileDetailView(DetailView):
    """Vista detallada de un archivo de datos"""
    model = DataFile
    template_name = 'data_import/detail.html'
    context_object_name = 'data_file'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener información de las columnas
        if self.object.columns:
            context['columns'] = self.object.columns.get('list', [])
            context['column_info'] = self.object.columns.get('info', {})
            context['rows'] = self.object.columns.get('rows', 0)
            
            # Crear formulario para selección de columnas
            context['column_form'] = ColumnSelectionForm(columns=context['columns'])
        
        # Obtener análisis anteriores
        context['analyses'] = self.object.analyses.all()
        
        return context

def preview_data(request, pk):
    """Vista para previsualizar los datos del archivo"""
    data_file = get_object_or_404(DataFile, pk=pk)
    
    try:
        # Leer las primeras filas del archivo
        df, _ = read_excel_file(data_file.file.path)
        preview_data = df.head(10).fillna('').to_dict(orient='records')
        columns = df.columns.tolist()
        
        return JsonResponse({
            'columns': columns,
            'data': preview_data,
            'total_rows': len(df)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def process_file(request, pk):
    """Vista para procesar el archivo y seleccionar columnas"""
    data_file = get_object_or_404(DataFile, pk=pk)
    
    if request.method == 'POST':
        # Obtener columnas seleccionadas del formulario
        selected_columns = []
        chart_type = request.POST.get('chart_type', 'line')
        x_axis = request.POST.get('x_axis', '')
        
        for key, value in request.POST.items():
            if key.startswith('column_') and value == 'on':
                column_name = key[7:]  # Quitar el prefijo 'column_'
                selected_columns.append(column_name)
        
        # Guardar selección para análisis
        analysis = DataAnalysis.objects.create(
            name=f"Análisis de {data_file.name} - {chart_type}",
            data_file=data_file,
            selected_columns=selected_columns,
            chart_type=chart_type,
            chart_config={
                'x_axis': x_axis,
                'title': f"Análisis de {data_file.name}",
            }
        )
        
        return redirect('data_visualization', analysis_id=analysis.id)
    
    # Si no es POST, redirigir a la vista detallada
    return redirect('data_file_detail', pk=pk)

def download_processed_data(request, pk):
    """Vista para descargar los datos procesados en formato CSV"""
    data_file = get_object_or_404(DataFile, pk=pk)
    
    try:
        df, _ = read_excel_file(data_file.file.path)
        
        # Generar CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{data_file.name}_processed.csv"'
        
        df.to_csv(path_or_buf=response, index=False, encoding='utf-8')
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar los datos: {str(e)}')
        return redirect('data_file_detail', pk=pk)