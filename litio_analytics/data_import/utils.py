# data_import/utils.py
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

def read_excel_file(file_path):
    """
    Lee un archivo Excel y devuelve un DataFrame de pandas
    Maneja múltiples hojas, valores vacíos y formatos especiales
    """
    try:
        # Intentar leer todas las hojas
        excel_data = pd.read_excel(file_path, sheet_name=None, na_values=['NA', 'N/A', ''], keep_default_na=True)
        
        # Si hay múltiples hojas, combinarlas en un solo DataFrame (opcional)
        if len(excel_data) > 1:
            # Por defecto, usamos la primera hoja
            df = excel_data[list(excel_data.keys())[0]]
            sheet_name = list(excel_data.keys())[0]
        else:
            # Si hay una sola hoja
            sheet_name = list(excel_data.keys())[0]
            df = excel_data[sheet_name]
        
        # Limpiar nombres de columnas (eliminar espacios y caracteres especiales)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Intentar convertir columnas numéricas (con manejo de errores)
        for col in df.columns:
            try:
                # Solo convertir si la mayoría de los valores no son NaN y parecen numéricos
                if df[col].notna().sum() > 0:
                    # Verificar si la columna parece contener mayormente números
                    sample = df[col].dropna().astype(str).str.replace(',', '.').str.replace(r'[^0-9.\-]', '', regex=True)
                    if sample.str.match(r'^-?\d*\.?\d*$').mean() > 0.7:  # Si más del 70% parecen números
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                # Si hay error, mantener la columna como está
                pass
        
        # Obtener información del DataFrame
        info = {
            'columns': df.columns.tolist(),
            'rows': len(df),
            'missing_values': df.isna().sum().to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'sheet_name': sheet_name,
            'sheets_available': list(excel_data.keys()),
        }
        
        return df, info
        
    except Exception as e:
        # Capturar cualquier error en la lectura
        error_info = {
            'error': str(e),
            'file_path': file_path,
        }
        raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

def get_column_statistics(df):
    """
    Obtiene estadísticas básicas para cada columna del DataFrame
    """
    stats = {}
    
    for column in df.columns:
        column_stats = {
            'type': str(df[column].dtype),
            'unique_values': df[column].nunique(),
            'missing_values': df[column].isna().sum(),
            'missing_percentage': round(df[column].isna().mean() * 100, 2),
        }
        
        # Estadísticas para columnas numéricas
        if pd.api.types.is_numeric_dtype(df[column]):
            column_stats.update({
                'min': float(df[column].min()) if not pd.isna(df[column].min()) else None,
                'max': float(df[column].max()) if not pd.isna(df[column].max()) else None,
                'mean': float(df[column].mean()) if not pd.isna(df[column].mean()) else None,
                'median': float(df[column].median()) if not pd.isna(df[column].median()) else None,
                'std': float(df[column].std()) if not pd.isna(df[column].std()) else None,
            })
        
        # Para columnas de texto
        elif df[column].dtype == 'object':
            # Obtener las frecuencias de los valores más comunes (top 5)
            value_counts = df[column].value_counts().head(5).to_dict()
            column_stats['most_common'] = value_counts
        
        stats[column] = column_stats
    
    return stats

def convert_df_to_json(df):
    """
    Convierte un DataFrame a formato JSON compatible con JavaScript
    Maneja tipos de datos especiales como fechas y valores NaN
    """
    # Convertir fechas a formato ISO
    for col in df.select_dtypes(include=['datetime64']).columns:
        df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Manejar NaN, infinitos, etc.
    df_json = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    
    # Convertir a registros (lista de diccionarios)
    records = df_json.to_dict(orient='records')
    
    return records