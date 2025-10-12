"""
Script para generar datos simulados de torres con información de riesgo.
Simula: amenaza estática, pendiente, y datos históricos de deslizamientos.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configurar semilla para reproducibilidad
np.random.seed(42)

def generar_datos_torres_extendido():
    """
    Genera CSV con torres y datos simulados de amenaza y pendiente.
    """
    print("=" * 70)
    print("🏗️  GENERANDO DATOS SIMULADOS DE TORRES")
    print("=" * 70)
    
    # Datos base de las torres
    torres_data = {
        'ID_Torre': [f'TORRE_{i:03d}' for i in range(1, 16)],
        'Nombre': [f'Torre {i}' for i in range(1, 16)],
        'Latitud': [
            6.642631, 6.858107, 6.841745, 6.356094, 6.710830,
            6.634446, 6.214130, 6.994109, 7.048910, 7.080816,
            7.152109, 7.186571, 7.225404, 7.271783, 7.314922
        ],
        'Longitud': [
            -71.814700, -71.902591, -71.391727, -70.825931, -70.666629,
            -71.314822, -71.946536, -72.023901, -72.153202, -72.214008,
            -72.350767, -72.429217, -72.464010, -72.456399, -72.502064
        ]
    }
    
    df = pd.DataFrame(torres_data)
    
    # SIMULAR AMENAZA ESTÁTICA (según SGC)
    # Distribución: 20% Muy Alta/Alta, 40% Media, 40% Baja/Muy Baja
    categorias_amenaza = ['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta']
    probabilidades = [0.15, 0.25, 0.40, 0.15, 0.05]
    
    df['Amenaza_SGC'] = np.random.choice(
        categorias_amenaza, 
        size=len(df), 
        p=probabilidades
    )
    
    # Mapear a valores numéricos (1-5)
    mapa_amenaza_num = {
        'Muy Baja': 1,
        'Baja': 2,
        'Media': 3,
        'Alta': 4,
        'Muy Alta': 5
    }
    df['Amenaza_Valor'] = df['Amenaza_SGC'].map(mapa_amenaza_num)
    
    # SIMULAR PENDIENTE (en grados)
    # Pendiente correlacionada con amenaza
    pendiente_base = {
        'Muy Baja': (0, 10),
        'Baja': (10, 20),
        'Media': (20, 30),
        'Alta': (30, 40),
        'Muy Alta': (40, 60)
    }
    
    pendientes = []
    for amenaza in df['Amenaza_SGC']:
        min_p, max_p = pendiente_base[amenaza]
        pendiente = np.random.uniform(min_p, max_p)
        pendientes.append(round(pendiente, 2))
    
    df['Pendiente_Grados'] = pendientes
    
    # Clasificar pendiente
    def clasificar_pendiente(p):
        if p < 15:
            return 'Baja'
        elif p < 30:
            return 'Media'
        else:
            return 'Alta'
    
    df['Pendiente_Clase'] = df['Pendiente_Grados'].apply(clasificar_pendiente)
    
    # SIMULAR ELEVACIÓN (metros sobre el nivel del mar)
    df['Elevacion_msnm'] = np.random.randint(500, 2500, size=len(df))
    
    # SIMULAR HISTORIAL DE EVENTOS (booleano)
    # 20% de torres han tenido eventos cercanos
    df['Historial_Eventos'] = np.random.choice([True, False], size=len(df), p=[0.2, 0.8])
    
    # SIMULAR DISTANCIA A DRENAJES (metros)
    # Torres cerca de drenajes tienen mayor riesgo
    df['Distancia_Drenaje_m'] = np.random.randint(10, 500, size=len(df))
    
    # SIMULAR TIPO DE SUELO
    tipos_suelo = ['Arcilloso', 'Limoso', 'Arenoso', 'Rocoso', 'Mixto']
    df['Tipo_Suelo'] = np.random.choice(tipos_suelo, size=len(df))
    
    # SIMULAR COBERTURA VEGETAL
    coberturas = ['Bosque Denso', 'Bosque Disperso', 'Pastos', 'Cultivos', 'Suelo Desnudo']
    df['Cobertura_Vegetal'] = np.random.choice(coberturas, size=len(df))
    
    # CALCULAR ÍNDICE DE RIESGO COMPUESTO (0-100)
    # Combina múltiples factores
    df['Indice_Riesgo'] = (
        df['Amenaza_Valor'] * 15 +  # Peso: 15%
        (df['Pendiente_Grados'] / 60 * 100) * 0.25 +  # Peso: 25%
        df['Historial_Eventos'].astype(int) * 20 +  # Peso: 20%
        (1 - df['Distancia_Drenaje_m'] / 500) * 15 +  # Peso: 15%
        np.random.uniform(0, 25, size=len(df))  # Factor aleatorio: 25%
    ).round(2)
    
    # Clasificar índice de riesgo
    def clasificar_riesgo(idx):
        if idx < 30:
            return 'Bajo'
        elif idx < 60:
            return 'Medio'
        else:
            return 'Alto'
    
    df['Clasificacion_Riesgo'] = df['Indice_Riesgo'].apply(clasificar_riesgo)
    
    return df


def generar_historial_eventos():
    """
    Genera CSV con historial simulado de eventos de deslizamiento.
    """
    print("\n🗓️  GENERANDO HISTORIAL DE EVENTOS...")
    
    # Generar 50 eventos históricos
    n_eventos = 50
    
    # Torres que tuvieron eventos (algunas se repiten)
    torres_con_eventos = [f'TORRE_{i:03d}' for i in [1, 3, 4, 7, 9, 10, 12, 14, 15]]
    
    eventos_data = {
        'Evento_ID': [f'EVT_{i:04d}' for i in range(1, n_eventos + 1)],
        'Fecha': pd.date_range(
            start='2020-01-01', 
            end='2024-12-31', 
            periods=n_eventos
        ).date,
        'ID_Torre': np.random.choice(torres_con_eventos, size=n_eventos),
        'Magnitud': np.random.choice(['Menor', 'Moderado', 'Severo'], size=n_eventos, p=[0.5, 0.3, 0.2]),
        'Precipitacion_72h_mm': np.random.uniform(50, 250, size=n_eventos).round(1),
        'Afecto_Infraestructura': np.random.choice([True, False], size=n_eventos, p=[0.3, 0.7]),
        'Tiempo_Respuesta_horas': np.random.randint(1, 48, size=n_eventos),
        'Costo_Reparacion_USD': np.random.randint(0, 50000, size=n_eventos)
    }
    
    df_eventos = pd.DataFrame(eventos_data)
    
    # Solo eventos que afectaron tienen costos
    df_eventos.loc[~df_eventos['Afecto_Infraestructura'], 'Costo_Reparacion_USD'] = 0
    
    return df_eventos


def generar_umbrales_lluvia():
    """
    Genera CSV con umbrales de lluvia por nivel de amenaza.
    """
    print("\n☔ GENERANDO MATRIZ DE UMBRALES DE LLUVIA...")
    
    umbrales_data = {
        'Amenaza_Nivel': ['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta'],
        'Umbral_Verde_mm': [200, 150, 120, 80, 60],
        'Umbral_Amarillo_mm': [250, 200, 150, 100, 80],
        'Umbral_Rojo_mm': [300, 250, 200, 120, 100],
        'Descripcion': [
            'Riesgo muy bajo - Monitoreo normal',
            'Riesgo bajo - Monitoreo normal',
            'Riesgo medio - Atención ante lluvias prolongadas',
            'Riesgo alto - Requiere monitoreo continuo',
            'Riesgo muy alto - Requiere vigilancia permanente'
        ]
    }
    
    df_umbrales = pd.DataFrame(umbrales_data)
    
    return df_umbrales


def main():
    """
    Ejecuta la generación completa de datos simulados.
    """
    # Crear directorios si no existen
    Path("../data/03_external").mkdir(parents=True, exist_ok=True)
    Path("../data/02_processed").mkdir(parents=True, exist_ok=True)
    
    # 1. Generar datos de torres
    df_torres = generar_datos_torres_extendido()
    ruta_torres = "../data/03_external/ubicacion_torres_completo.csv"
    df_torres.to_csv(ruta_torres, index=False)
    
    print(f"\n✅ Datos de torres guardados en:")
    print(f"   {ruta_torres}")
    print(f"\n📊 Resumen de torres:")
    print(df_torres[['ID_Torre', 'Amenaza_SGC', 'Pendiente_Grados', 'Clasificacion_Riesgo']].head(10))
    
    # 2. Generar historial de eventos
    df_eventos = generar_historial_eventos()
    ruta_eventos = "../data/03_external/historial_eventos.csv"
    df_eventos.to_csv(ruta_eventos, index=False)
    
    print(f"\n✅ Historial de eventos guardado en:")
    print(f"   {ruta_eventos}")
    print(f"   Total eventos: {len(df_eventos)}")
    
    # 3. Generar umbrales de lluvia
    df_umbrales = generar_umbrales_lluvia()
    ruta_umbrales = "../data/03_external/umbrales_lluvia.csv"
    df_umbrales.to_csv(ruta_umbrales, index=False)
    
    print(f"\n✅ Umbrales de lluvia guardados en:")
    print(f"   {ruta_umbrales}")
    
    # 4. Crear versión simplificada para compatibilidad
    df_simple = df_torres[['ID_Torre', 'Nombre', 'Latitud', 'Longitud']].copy()
    ruta_simple = "../data/03_external/ubicacion_torres.csv"
    df_simple.to_csv(ruta_simple, index=False)
    
    print(f"\n✅ Versión simplificada guardada en:")
    print(f"   {ruta_simple}")
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✅ GENERACIÓN DE DATOS COMPLETADA")
    print("=" * 70)
    print("\n📁 Archivos generados:")
    print(f"   1. {ruta_torres} - Datos completos de torres")
    print(f"   2. {ruta_eventos} - Historial de eventos")
    print(f"   3. {ruta_umbrales} - Matriz de umbrales")
    print(f"   4. {ruta_simple} - Versión simple de torres")
    
    print("\n📊 Estadísticas:")
    print(f"   Total torres: {len(df_torres)}")
    print(f"   Distribución de amenaza:")
    for nivel, count in df_torres['Amenaza_SGC'].value_counts().items():
        print(f"      • {nivel}: {count} torres")
    
    print(f"\n   Distribución de riesgo compuesto:")
    for nivel, count in df_torres['Clasificacion_Riesgo'].value_counts().items():
        print(f"      • {nivel}: {count} torres")
    
    print("\n🚀 SIGUIENTE PASO: Ejecutar la aplicación de Streamlit")
    print("   streamlit run app_dashboard.py")


if __name__ == "__main__":
    main()