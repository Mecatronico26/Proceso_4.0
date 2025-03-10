# data_visualization/views.py
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.generic import DetailView
from data_import.models import DataAnalysis, DataFile
from data_import.utils import read_excel_file, convert_df_to_json

def generate_visualization(request, analysis_id):
    """Vista principal para la visualización de datos"""
    analysis = get_object_or_404(DataAnalysis, pk=analysis_id)
    data_file = analysis.data_file
    
    try:
        # Leer el archivo
        df, _ = read_excel_file(data_file.file.path)
        
        # Seleccionar columnas para el análisis
        selected_columns = analysis.selected_columns
        
        # Verificar si existe el eje X especificado
        x_axis = analysis.chart_config.get('x_axis', '')
        
        # Filtrar columnas válidas (pueden haber cambiado desde que se creó el análisis)
        valid_columns = [col for col in selected_columns if col in df.columns]
        
        if not valid_columns:
            messages.error(request, 'No hay columnas válidas seleccionadas para el análisis.')
            return redirect('data_file_detail', pk=data_file.pk)
        
        # Determinar tipo de gráfico y generar visualización
        chart_type = analysis.chart_type
        
        # Datos para la visualización
        if x_axis and x_axis in df.columns:
            # Caso con eje X especificado
            plot_data = df[[x_axis] + [col for col in valid_columns if col != x_axis]]
            
            # Generar figura según el tipo de gráfico
            if chart_type == 'line':
                fig = px.line(plot_data, x=x_axis, y=valid_columns, title=analysis.name)
            elif chart_type == 'bar':
                fig = px.bar(plot_data, x=x_axis, y=valid_columns, title=analysis.name)
            elif chart_type == 'scatter':
                fig = px.scatter(plot_data, x=x_axis, y=valid_columns, title=analysis.name)
            elif chart_type == 'box':
                fig = px.box(plot_data, x=x_axis, y=valid_columns, title=analysis.name)
            elif chart_type == 'histogram':
                fig = px.histogram(plot_data, x=x_axis, title=analysis.name)
            elif chart_type == 'heatmap':
                # Para mapas de calor, se necesita una matriz de correlación
                corr_df = plot_data.select_dtypes(include=['number']).corr()
                fig = px.imshow(corr_df, text_auto=True, title=f"Mapa de correlación - {analysis.name}")
            else:
                # Tipo de gráfico por defecto
                fig = px.line(plot_data, x=x_axis, y=valid_columns, title=analysis.name)
        else:
            # Caso sin eje X específico (solo columnas numéricas)
            numeric_df = df[valid_columns].select_dtypes(include=['number'])
            
            if numeric_df.empty:
                messages.warning(request, 'No hay columnas numéricas para visualizar. Seleccione algunas columnas numéricas.')
                fig = go.Figure()
                fig.add_annotation(
                    text="No hay datos numéricos para visualizar",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
            else:
                if chart_type == 'line':
                    fig = px.line(numeric_df, title=analysis.name)
                elif chart_type == 'bar':
                    fig = px.bar(numeric_df, title=analysis.name)
                elif chart_type == 'scatter':
                    # Para scatter necesitamos al menos dos columnas
                    if len(numeric_df.columns) >= 2:
                        fig = px.scatter(numeric_df, x=numeric_df.columns[0], y=numeric_df.columns[1:], title=analysis.name)
                    else:
                        fig = px.scatter(numeric_df, title=analysis.name)
                elif chart_type == 'pie':
                    # Para pie chart, tomamos la primera columna
                    if len(numeric_df.columns) > 0:
                        fig = px.pie(numeric_df, values=numeric_df.columns[0], names=numeric_df.index, title=analysis.name)
                    else:
                        fig = go.Figure()
                elif chart_type == 'histogram':
                    fig = px.histogram(numeric_df, title=analysis.name)
                elif chart_type == 'box':
                    fig = px.box(numeric_df, title=analysis.name)
                elif chart_type == 'heatmap':
                    # Mapa de calor de correlación
                    corr_df = numeric_df.corr()
                    fig = px.imshow(corr_df, text_auto=True, title=f"Mapa de correlación - {analysis.name}")
                else:
                    # Tipo de gráfico por defecto
                    fig = px.line(numeric_df, title=analysis.name)
        
        # Personalizar diseño
        fig.update_layout(
            template='plotly_white',
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        
        # Convertir figura a JSON para JavaScript
        chart_json = json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)
        
        # Obtener estadísticas básicas
        stats = {}
        for col in valid_columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats[col] = {
                    'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    'median': float(df[col].median()) if not pd.isna(df[col].median()) else None,
                    'std': float(df[col].std()) if not pd.isna(df[col].std()) else None,
                }
        
        # Datos para la tabla
        table_data = df[valid_columns].head(100)
        
        # Guardamos los datos procesados para posibles exportaciones
        raw_data = convert_df_to_json(df[valid_columns])
        
        return render(request, 'data_visualization/visualization.html', {
            'analysis': analysis,
            'data_file': data_file,
            'chart_json': chart_json,
            'chart_type': chart_type,
            'columns': valid_columns,
            'stats': stats,
            'table_data': table_data.to_dict(orient='records'),
            'table_columns': table_data.columns.tolist(),
            'raw_data': json.dumps(raw_data[:1000]),  # Limitar a 1000 filas para JSON
        })
        
    except Exception as e:
        messages.error(request, f'Error al generar la visualización: {str(e)}')
        return redirect('data_file_detail', pk=data_file.pk)

def export_visualization(request, analysis_id, format='png'):
    """Exportar la visualización en diferentes formatos"""
    analysis = get_object_or_404(DataAnalysis, pk=analysis_id)
    
    try:
        # Generar visualización (similar a generate_visualization)
        df, _ = read_excel_file(analysis.data_file.file.path)
        selected_columns = analysis.selected_columns
        x_axis = analysis.chart_config.get('x_axis', '')
        valid_columns = [col for col in selected_columns if col in df.columns]
        
        # Generar la figura (código similar al de arriba)
        # Este es un ejemplo simplificado
        if x_axis and x_axis in df.columns:
            fig = px.line(df, x=x_axis, y=valid_columns, title=analysis.name)
        else:
            numeric_df = df[valid_columns].select_dtypes(include=['number'])
            fig = px.line(numeric_df, title=analysis.name)
        
        # Exportar según el formato solicitado
        if format == 'png':
            img_bytes = fig.to_image(format='png')
            response = HttpResponse(img_bytes, content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="{analysis.name}.png"'
        elif format == 'pdf':
            img_bytes = fig.to_image(format='pdf')
            response = HttpResponse(img_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{analysis.name}.pdf"'
        elif format == 'svg':
            img_bytes = fig.to_image(format='svg')
            response = HttpResponse(img_bytes, content_type='image/svg+xml')
            response['Content-Disposition'] = f'attachment; filename="{analysis.name}.svg"'
        elif format == 'csv':
            # Exportar datos en CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{analysis.name}.csv"'
            df[valid_columns].to_csv(path_or_buf=response, index=False)
        elif format == 'excel':
            # Exportar datos en Excel
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{analysis.name}.xlsx"'
            df[valid_columns].to_excel(response, index=False)
        else:
            return JsonResponse({'error': 'Formato no soportado'}, status=400)
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def update_visualization(request, analysis_id):
    """Actualizar configuración de la visualización"""
    analysis = get_object_or_404(DataAnalysis, pk=analysis_id)
    
    if request.method == 'POST':
        try:
            # Actualizar configuración desde el formulario
            chart_type = request.POST.get('chart_type', analysis.chart_type)
            title = request.POST.get('title', analysis.name)
            x_axis = request.POST.get('x_axis', analysis.chart_config.get('x_axis', ''))
            
            # Actualizar columnas seleccionadas
            selected_columns = []
            for key, value in request.POST.items():
                if key.startswith('column_') and value == 'on':
                    column_name = key[7:]  # Quitar el prefijo 'column_'
                    selected_columns.append(column_name)
            
            # Si no hay columnas seleccionadas, mantener las existentes
            if not selected_columns:
                selected_columns = analysis.selected_columns
            
            # Actualizar objeto de análisis
            analysis.name = title
            analysis.chart_type = chart_type
            analysis.selected_columns = selected_columns
            analysis.chart_config = {
                'x_axis': x_axis,
                'title': title,
            }
            analysis.save()
            
            messages.success(request, 'Visualización actualizada correctamente.')
        
        except Exception as e:
            messages.error(request, f'Error al actualizar la visualización: {str(e)}')
        
        return redirect('data_visualization', analysis_id=analysis_id)
    
    # Si no es POST, redirigir a la visualización
    return redirect('data_visualization', analysis_id=analysis_id)

def delete_analysis(request, analysis_id):
    """Eliminar un análisis"""
    analysis = get_object_or_404(DataAnalysis, pk=analysis_id)
    data_file_id = analysis.data_file.id
    
    try:
        analysis.delete()
        messages.success(request, 'Análisis eliminado correctamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el análisis: {str(e)}')
    
    return redirect('data_file_detail', pk=data_file_id)