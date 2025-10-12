"""
Script para preprocesar datos de amenaza de deslizamientos.
Ejecutar ANTES de lanzar la aplicación Streamlit.
"""

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.pyplot as plt


def clasificar_raster_amenaza(ruta_in, ruta_out):
    """
    Lee un raster de amenaza continuo y lo clasifica en tres niveles.
    
    Args:
        ruta_in: Ruta al raster original con valores continuos
        ruta_out: Ruta donde guardar el raster clasificado
    """
    print("📊 Paso 1: Analizando distribución de valores...")
    
    with rasterio.open(ruta_in) as src:
        data = src.read(1)
        NoData_value = src.nodata
        
    # Filtrar valores NoData
    valores_reales = data[data != NoData_value]
    
    # Calcular umbrales usando cuantiles
    umbral_bajo = np.quantile(valores_reales, 0.33)
    umbral_alto = np.quantile(valores_reales, 0.66)
    
    print(f"✅ Umbral para Amenaza BAJA: Valores <= {umbral_bajo:.2f}")
    print(f"✅ Umbral para Amenaza MEDIA: Valores > {umbral_bajo:.2f} y <= {umbral_alto:.2f}")
    print(f"✅ Umbral para Amenaza ALTA: Valores > {umbral_alto:.2f}")
    
    # Crear histograma
    plt.figure(figsize=(10, 6))
    plt.hist(valores_reales, bins=50, color='skyblue', edgecolor='black')
    plt.axvline(umbral_bajo, color='green', linestyle='--', label='Umbral Bajo')
    plt.axvline(umbral_alto, color='red', linestyle='--', label='Umbral Alto')
    plt.title('Distribución de Valores de Susceptibilidad de Amenaza')
    plt.xlabel('Valor de Susceptibilidad')
    plt.ylabel('Frecuencia (Número de Píxeles)')
    plt.legend()
    plt.grid(True, alpha=0.5)
    plt.savefig('histograma_amenaza.png', dpi=150, bbox_inches='tight')
    print("✅ Histograma guardado: histograma_amenaza.png")
    
    # Clasificar
    print("\n🔄 Paso 2: Clasificando raster...")
    classified_data = np.zeros(data.shape, dtype=np.uint8)
    classified_data[(data > NoData_value) & (data <= umbral_bajo)] = 1  # Baja
    classified_data[(data > umbral_bajo) & (data <= umbral_alto)] = 2   # Media
    classified_data[data > umbral_alto] = 3                              # Alta
    
    # Guardar raster clasificado
    with rasterio.open(ruta_in) as src:
        profile = src.profile
        profile['driver'] = 'GTiff'
        profile.update(dtype=rasterio.uint8, count=1, nodata=0)
    
    with rasterio.open(ruta_out, 'w', **profile) as dst:
        dst.write(classified_data, 1)
    
    print(f"✅ Raster clasificado guardado en: {ruta_out}")
    
    return umbral_bajo, umbral_alto


def reproyectar_raster_wgs84(ruta_in, ruta_out):
    """
    Reproyecta el raster clasificado a WGS84 (EPSG:4326) para usar con Folium.
    
    Args:
        ruta_in: Raster clasificado en proyección original
        ruta_out: Raster reproyectado a WGS84
    """
    print("\n🌍 Paso 3: Reproyectando a WGS84...")
    
    dst_crs = "EPSG:4326"
    
    with rasterio.open(ruta_in) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        
        kwargs = src.meta.copy()
        kwargs.update({
            'driver': 'GTiff',
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        
        with rasterio.open(ruta_out, 'w', **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest
            )
    
    print(f"✅ Raster reproyectado guardado en: {ruta_out}")


def extraer_valores_torres(ruta_torres_csv, ruta_raster, ruta_salida):
    """
    Extrae los valores de amenaza del raster para cada ubicación de torre.
    
    Args:
        ruta_torres_csv: CSV con columnas ID_Torre, Latitud, Longitud
        ruta_raster: Raster clasificado en WGS84
        ruta_salida: CSV de salida con información de amenaza por torre
    """
    print("\n📍 Paso 4: Extrayendo valores de amenaza para torres...")
    
    try:
        torres_df = pd.read_csv(ruta_torres_csv)
        print(f"✅ Cargadas {len(torres_df)} torres desde {ruta_torres_csv}")
    except FileNotFoundError:
        print("⚠️ Archivo de torres no encontrado. Creando datos de ejemplo...")
        torres_df = pd.DataFrame({
            'ID_Torre': ['TORRE_001', 'TORRE_002', 'TORRE_003', 'TORRE_004'],
            'Nombre': ['Torre Norte', 'Torre Sur', 'Torre Este', 'Torre Oeste'],
            'Latitud': [7.08, 7.10, 6.356094, 7.05],
            'Longitud': [-72.25, -72.28, -70.825931, -72.20]
        })
    
    # Extraer coordenadas
    coords = [(x, y) for x, y in zip(torres_df['Longitud'], torres_df['Latitud'])]
    
    # Muestrear raster
    with rasterio.open(ruta_raster) as src:
        valores_raster = [val[0] for val in src.sample(coords)]
    
    # Añadir resultados
    torres_df['Amenaza_Valor'] = valores_raster
    
    # Mapear a etiquetas
    mapa_amenaza = {1: 'Baja', 2: 'Media', 3: 'Alta', 0: 'Sin Datos'}
    torres_df['Amenaza_Nivel'] = torres_df['Amenaza_Valor'].map(mapa_amenaza)
    
    # Guardar
    torres_df.to_csv(ruta_salida, index=False)
    print(f"✅ Datos de torres con amenaza guardados en: {ruta_salida}")
    
    # Resumen
    print("\n📊 Resumen de clasificación de torres:")
    print(torres_df[['ID_Torre', 'Amenaza_Nivel']].to_string(index=False))
    print(f"\n{torres_df['Amenaza_Nivel'].value_counts().to_dict()}")


def pipeline_completo():
    """
    Ejecuta todo el pipeline de procesamiento.
    """
    print("=" * 60)
    print("🚀 INICIANDO PIPELINE DE PROCESAMIENTO DE DATOS")
    print("=" * 60)
    
    # Rutas de archivos
    RUTA_RASTER_ORIGINAL = "data/01_raw/amenaza_arauca/arc/w001001.adf"
    RUTA_RASTER_CLASIFICADO = "data/02_processed/amenaza_arauca_clasificado.tif"
    RUTA_RASTER_WGS84 = "data/02_processed/amenaza_arauca_clasificado_wgs84.tif"
    RUTA_TORRES_INPUT = "data/03_external/ubicacion_torres.csv"
    RUTA_TORRES_OUTPUT = "data/02_processed/torres_con_amenaza.csv"
    
    try:
        # Paso 1: Clasificar raster
        clasificar_raster_amenaza(RUTA_RASTER_ORIGINAL, RUTA_RASTER_CLASIFICADO)
        
        # Paso 2: Reproyectar
        reproyectar_raster_wgs84(RUTA_RASTER_CLASIFICADO, RUTA_RASTER_WGS84)
        
        # Paso 3: Extraer valores para torres
        extraer_valores_torres(RUTA_TORRES_INPUT, RUTA_RASTER_WGS84, RUTA_TORRES_OUTPUT)
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n🚀 Ahora puedes ejecutar la aplicación Streamlit:")
        print("   streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        raise


if __name__ == "__main__":
    pipeline_completo()