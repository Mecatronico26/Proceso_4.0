# dashboard/views.py
from django.shortcuts import render, redirect
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from data_import.models import DataFile, DataAnalysis

def index(request):
    """Vista principal del dashboard"""
    
    # Estadísticas generales
    total_files = DataFile.objects.count()
    total_analyses = DataAnalysis.objects.count()
    
    # Archivos recientes
    recent_files = DataFile.objects.order_by('-uploaded_at')[:5]
    
    # Análisis recientes
    recent_analyses = DataAnalysis.objects.select_related('data_file').order_by('-created_at')[:5]
    
    # Actividad reciente (últimos 7 días)
    last_week = timezone.now() - timedelta(days=7)
    activity_files = DataFile.objects.filter(uploaded_at__gte=last_week).count()
    activity_analyses = DataAnalysis.objects.filter(created_at__gte=last_week).count()
    
    # Archivos por día (para gráfica)
    files_by_day = (
        DataFile.objects.filter(uploaded_at__gte=last_week)
        .extra({'date': "date(uploaded_at)"})
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    # Formatear para la gráfica
    chart_data = []
    for item in files_by_day:
        chart_data.append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        })
    
    context = {
        'total_files': total_files,
        'total_analyses': total_analyses,
        'recent_files': recent_files,
        'recent_analyses': recent_analyses,
        'activity_files': activity_files,
        'activity_analyses': activity_analyses,
        'chart_data': chart_data,
    }
    
    return render(request, 'dashboard/index.html', context)