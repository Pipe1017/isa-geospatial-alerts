"""
Dashboard Interactivo de Alertas de Deslizamientos
Sistema de monitoreo en tiempo real para torres de transmisión
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="SAT Deslizamientos ISA",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

@st.cache_data
def cargar_torres():
    """Carga datos completos de torres"""
    try:
        df = pd.read_csv("../data/03_external/ubicacion_torres_completo.csv")
        return df
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo de torres. Ejecuta primero: python simular_datos.py")
        st.stop()

@st.cache_data
def cargar_umbrales():
    """Carga matriz de umbrales de lluvia"""
    try:
        df = pd.read_csv("../data/03_external/umbrales_lluvia.csv")
        return df
    except FileNotFoundError:
        # Umbrales por defecto
        return pd.DataFrame({
            'Amenaza_Nivel': ['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta'],
            'Umbral_Verde_mm': [200, 150, 120, 80, 60],
            'Umbral_Amarillo_mm': [250, 200, 150, 100, 80],
            'Umbral_Rojo_mm': [300, 250, 200, 120, 100]
        })

@st.cache_data
def cargar_historial_eventos():
    """Carga historial de eventos"""
    try:
        df = pd.read_csv("../data/03_external/historial_eventos.csv")
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

# ============================================================================
# FUNCIONES DE API Y PROCESAMIENTO
# ============================================================================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def obtener_lluvia_torre(lat, lon, dias=3):
    """Obtiene datos de precipitación de Open-Meteo"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=dias)
    
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=precipitation"
        f"&start_date={start_date.strftime('%Y-%m-%d')}"
        f"&end_date={end_date.strftime('%Y-%m-%d')}"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])
            df['time'] = pd.to_datetime(df['time'])
            return df
        return None
    except:
        return None

def calcular_nivel_alerta(amenaza, lluvia_72h, umbrales_df):
    """Calcula nivel de alerta usando matriz de umbrales"""
    umbral = umbrales_df[umbrales_df['Amenaza_Nivel'] == amenaza]
    
    if umbral.empty:
        return 'VERDE', '🟢', 0
    
    umbral_rojo = umbral['Umbral_Rojo_mm'].values[0]
    umbral_amarillo = umbral['Umbral_Amarillo_mm'].values[0]
    
    if lluvia_72h >= umbral_rojo:
        return 'ROJA', '🔴', 3
    elif lluvia_72h >= umbral_amarillo:
        return 'AMARILLA', '🟡', 2
    else:
        return 'VERDE', '🟢', 1

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

# Título y descripción
st.title("🛰️ Sistema de Alerta Temprana de Deslizamientos")
st.markdown("""
Sistema de monitoreo en tiempo real que combina **amenaza estática**, **pendiente del terreno** 
y **precipitación actual** para generar alertas operacionales.
""")

# ============================================================================
# SIDEBAR - CONFIGURACIÓN
# ============================================================================

st.sidebar.header("⚙️ Configuración")

# Cargar datos
torres_df = cargar_torres()
umbrales_df = cargar_umbrales()
eventos_df = cargar_historial_eventos()

# Selector de torre
torre_seleccionada = st.sidebar.selectbox(
    "📍 Seleccionar Torre:",
    torres_df['ID_Torre'],
    help="Selecciona una torre para ver detalles"
)

# Filtros
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros")

filtro_amenaza = st.sidebar.multiselect(
    "Nivel de Amenaza:",
    ['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta'],
    default=['Alta', 'Muy Alta']
)

filtro_riesgo = st.sidebar.multiselect(
    "Clasificación de Riesgo:",
    ['Bajo', 'Medio', 'Alto'],
    default=['Alto']
)

# Botón de actualización
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Datos de Lluvia", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"🕐 Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# OBTENER DATOS DE LLUVIA PARA TODAS LAS TORRES
# ============================================================================

with st.spinner('🌧️ Obteniendo datos de precipitación...'):
    datos_lluvia = []
    
    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (i, torre) in enumerate(torres_df.iterrows()):
        progress = (idx + 1) / len(torres_df)
        progress_bar.progress(progress)
        status_text.text(f"Consultando {torre['ID_Torre']}... ({idx+1}/{len(torres_df)})")
        
        df_lluvia = obtener_lluvia_torre(torre['Latitud'], torre['Longitud'])
        
        if df_lluvia is not None:
            lluvia_72h = df_lluvia['precipitation'].sum()
            lluvia_24h = df_lluvia.tail(24)['precipitation'].sum()
        else:
            lluvia_72h = 0
            lluvia_24h = 0
        
        datos_lluvia.append({
            'ID_Torre': torre['ID_Torre'],
            'Lluvia_72h': lluvia_72h,
            'Lluvia_24h': lluvia_24h
        })
    
    progress_bar.empty()
    status_text.empty()

# Combinar con datos de torres
df_lluvia = pd.DataFrame(datos_lluvia)
torres_df = torres_df.merge(df_lluvia, on='ID_Torre')

# Calcular alertas
torres_df[['Nivel_Alerta', 'Emoji_Alerta', 'Prioridad']] = torres_df.apply(
    lambda row: pd.Series(calcular_nivel_alerta(
        row['Amenaza_SGC'], 
        row['Lluvia_72h'], 
        umbrales_df
    )), axis=1
)

# Ordenar por prioridad
torres_df = torres_df.sort_values('Prioridad', ascending=False)

# ============================================================================
# SECCIÓN 1: RESUMEN EJECUTIVO
# ============================================================================

st.header("📊 Resumen Ejecutivo")

col1, col2, col3, col4, col5 = st.columns(5)

n_total = len(torres_df)
n_rojas = (torres_df['Nivel_Alerta'] == 'ROJA').sum()
n_amarillas = (torres_df['Nivel_Alerta'] == 'AMARILLA').sum()
n_verdes = (torres_df['Nivel_Alerta'] == 'VERDE').sum()
n_alto_riesgo = (torres_df['Clasificacion_Riesgo'] == 'Alto').sum()

col1.metric("🏗️ Total Torres", n_total)
col2.metric("🔴 Alertas Rojas", n_rojas, delta=f"{n_rojas/n_total*100:.1f}%")
col3.metric("🟡 Alertas Amarillas", n_amarillas, delta=f"{n_amarillas/n_total*100:.1f}%")
col4.metric("🟢 Sin Alertas", n_verdes, delta=f"{n_verdes/n_total*100:.1f}%")
col5.metric("⚠️ Alto Riesgo Base", n_alto_riesgo)

# ============================================================================
# SECCIÓN 2: MAPA INTERACTIVO
# ============================================================================

st.markdown("---")
st.header("🗺️ Mapa de Torres con Alertas")

# Crear mapa
fig_mapa = go.Figure()

color_map = {'VERDE': 'green', 'AMARILLA': 'orange', 'ROJA': 'red'}
size_map = {'VERDE': 12, 'AMARILLA': 16, 'ROJA': 20}

for nivel in ['VERDE', 'AMARILLA', 'ROJA']:
    torres_nivel = torres_df[torres_df['Nivel_Alerta'] == nivel]
    
    if not torres_nivel.empty:
        fig_mapa.add_trace(go.Scattermapbox(
            lat=torres_nivel['Latitud'],
            lon=torres_nivel['Longitud'],
            mode='markers',
            marker=dict(
                size=torres_nivel['Nivel_Alerta'].map(size_map),
                color=color_map[nivel]
            ),
            text=torres_nivel.apply(
                lambda x: (
                    f"<b>{x['ID_Torre']}: {x['Nombre']}</b><br>"
                    f"Amenaza: {x['Amenaza_SGC']}<br>"
                    f"Pendiente: {x['Pendiente_Grados']:.1f}°<br>"
                    f"Lluvia 72h: {x['Lluvia_72h']:.1f}mm<br>"
                    f"Riesgo: {x['Clasificacion_Riesgo']}<br>"
                    f"<b>Alerta: {x['Nivel_Alerta']}</b>"
                ), axis=1
            ),
            hoverinfo='text',
            name=f'{nivel}'
        ))

fig_mapa.update_layout(
    mapbox=dict(
        style='open-street-map',
        center=dict(
            lat=torres_df['Latitud'].mean(),
            lon=torres_df['Longitud'].mean()
        ),
        zoom=8
    ),
    height=500,
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=True
)

st.plotly_chart(fig_mapa, use_container_width=True)

# ============================================================================
# SECCIÓN 3: MATRIZ DE RIESGO
# ============================================================================

st.markdown("---")
st.header("📈 Matriz de Riesgo: Amenaza vs Precipitación")

col1, col2 = st.columns([2, 1])

with col1:
    # Scatter plot interactivo
    fig_matriz = px.scatter(
        torres_df,
        x='Lluvia_72h',
        y='Amenaza_Valor',
        color='Nivel_Alerta',
        color_discrete_map=color_map,
        size='Pendiente_Grados',
        size_max=20,
        hover_data={
            'ID_Torre': True,
            'Nombre': True,
            'Amenaza_SGC': True,
            'Pendiente_Grados': ':.1f',
            'Lluvia_72h': ':.1f',
            'Clasificacion_Riesgo': True,
            'Amenaza_Valor': False
        },
        labels={
            'Lluvia_72h': 'Precipitación Acumulada 72h (mm)',
            'Amenaza_Valor': 'Nivel de Amenaza'
        },
        title='Matriz de Riesgo Combinado'
    )
    
    # Agregar zonas de riesgo
    max_lluvia = torres_df['Lluvia_72h'].max() * 1.1
    fig_matriz.add_vrect(x0=0, x1=80, fillcolor="green", opacity=0.1, line_width=0)
    fig_matriz.add_vrect(x0=80, x1=120, fillcolor="yellow", opacity=0.1, line_width=0)
    fig_matriz.add_vrect(x0=120, x1=max_lluvia, fillcolor="red", opacity=0.1, line_width=0)
    
    # Ajustar eje Y
    fig_matriz.update_yaxes(
        tickmode='array',
        tickvals=[1, 2, 3, 4, 5],
        ticktext=['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta']
    )
    
    fig_matriz.update_layout(height=500)
    st.plotly_chart(fig_matriz, use_container_width=True)

with col2:
    st.subheader("📋 Matriz de Umbrales")
    st.dataframe(
        umbrales_df.style.background_gradient(
            subset=['Umbral_Amarillo_mm', 'Umbral_Rojo_mm'],
            cmap='YlOrRd'
        ),
        use_container_width=True,
        hide_index=True
    )

# ============================================================================
# SECCIÓN 4: ANÁLISIS DE TORRE SELECCIONADA
# ============================================================================

st.markdown("---")
st.header(f"🔍 Análisis Detallado: {torre_seleccionada}")

torre_info = torres_df[torres_df['ID_Torre'] == torre_seleccionada].iloc[0]

# Métricas de la torre
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("📍 Ubicación", f"{torre_info['Latitud']:.3f}°, {torre_info['Longitud']:.3f}°")
col2.metric("🏔️ Amenaza", torre_info['Amenaza_SGC'])
col3.metric("📐 Pendiente", f"{torre_info['Pendiente_Grados']:.1f}°")
col4.metric("💧 Lluvia 72h", f"{torre_info['Lluvia_72h']:.1f}mm")
col5.metric("🚨 Alerta", f"{torre_info['Emoji_Alerta']} {torre_info['Nivel_Alerta']}")

# Información adicional
with st.expander("ℹ️ Información Adicional", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Características del Terreno:**")
        st.write(f"- Elevación: {torre_info['Elevacion_msnm']} msnm")
        st.write(f"- Pendiente: {torre_info['Pendiente_Clase']}")
        st.write(f"- Tipo de suelo: {torre_info['Tipo_Suelo']}")
        st.write(f"- Cobertura vegetal: {torre_info['Cobertura_Vegetal']}")
    
    with col2:
        st.write("**Factores de Riesgo:**")
        st.write(f"- Índice de riesgo: {torre_info['Indice_Riesgo']:.1f}/100")
        st.write(f"- Clasificación: {torre_info['Clasificacion_Riesgo']}")
        st.write(f"- Distancia a drenajes: {torre_info['Distancia_Drenaje_m']}m")
        historial = "Sí ✓" if torre_info['Historial_Eventos'] else "No"
        st.write(f"- Eventos previos: {historial}")
    
    with col3:
        st.write("**Precipitación:**")
        st.write(f"- Últimas 24h: {torre_info['Lluvia_24h']:.1f}mm")
        st.write(f"- Últimas 72h: {torre_info['Lluvia_72h']:.1f}mm")
        
        # Obtener umbrales para esta torre
        umbral_torre = umbrales_df[umbrales_df['Amenaza_Nivel'] == torre_info['Amenaza_SGC']]
        if not umbral_torre.empty:
            st.write(f"- Umbral amarillo: {umbral_torre['Umbral_Amarillo_mm'].values[0]}mm")
            st.write(f"- Umbral rojo: {umbral_torre['Umbral_Rojo_mm'].values[0]}mm")

# Gráfico de precipitación para la torre
df_lluvia_torre = obtener_lluvia_torre(torre_info['Latitud'], torre_info['Longitud'], dias=7)

if df_lluvia_torre is not None:
    # Calcular acumulado rodante de 72h
    df_lluvia_torre['precip_acum_72h'] = df_lluvia_torre['precipitation'].rolling(
        window=72, min_periods=1
    ).sum()
    
    # Calcular nivel de alerta para cada punto en el tiempo
    def calcular_alerta_temporal(lluvia, amenaza):
        umbral = umbrales_df[umbrales_df['Amenaza_Nivel'] == amenaza]
        if umbral.empty:
            return 'VERDE'
        
        umbral_rojo = umbral['Umbral_Rojo_mm'].values[0]
        umbral_amarillo = umbral['Umbral_Amarillo_mm'].values[0]
        
        if lluvia >= umbral_rojo:
            return 'ROJA'
        elif lluvia >= umbral_amarillo:
            return 'AMARILLA'
        else:
            return 'VERDE'
    
    df_lluvia_torre['nivel_alerta_temporal'] = df_lluvia_torre['precip_acum_72h'].apply(
        lambda x: calcular_alerta_temporal(x, torre_info['Amenaza_SGC'])
    )
    
    # Crear dos subgráficos
    from plotly.subplots import make_subplots
    
    fig_lluvia = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            'Evolución de Precipitación Acumulada (72h)',
            'Evolución del Nivel de Alerta en el Tiempo'
        ),
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4]
    )
    
    # GRÁFICO 1: Línea de precipitación acumulada
    fig_lluvia.add_trace(
        go.Scatter(
            x=df_lluvia_torre['time'],
            y=df_lluvia_torre['precip_acum_72h'],
            mode='lines',
            name='Lluvia Acumulada 72h',
            line=dict(color='steelblue', width=2),
            fill='tozeroy',
            fillcolor='rgba(70, 130, 180, 0.2)'
        ),
        row=1, col=1
    )
    
    # Agregar líneas de umbrales
    if not umbral_torre.empty:
        umbral_amarillo = umbral_torre['Umbral_Amarillo_mm'].values[0]
        umbral_rojo = umbral_torre['Umbral_Rojo_mm'].values[0]
        
        # Líneas horizontales de umbrales
        fig_lluvia.add_hline(
            y=umbral_amarillo,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text=f"Umbral Amarillo ({umbral_amarillo}mm)",
            annotation_position="right",
            row=1, col=1
        )
        fig_lluvia.add_hline(
            y=umbral_rojo,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"Umbral Rojo ({umbral_rojo}mm)",
            annotation_position="right",
            row=1, col=1
        )
        
        # Resaltar momentos de alerta
        alertas_rojas = df_lluvia_torre[df_lluvia_torre['nivel_alerta_temporal'] == 'ROJA']
        alertas_amarillas = df_lluvia_torre[df_lluvia_torre['nivel_alerta_temporal'] == 'AMARILLA']
        
        if not alertas_rojas.empty:
            fig_lluvia.add_trace(
                go.Scatter(
                    x=alertas_rojas['time'],
                    y=alertas_rojas['precip_acum_72h'],
                    mode='markers',
                    name='Alerta ROJA',
                    marker=dict(color='red', size=10, symbol='x', line=dict(width=2, color='darkred'))
                ),
                row=1, col=1
            )
        
        if not alertas_amarillas.empty:
            fig_lluvia.add_trace(
                go.Scatter(
                    x=alertas_amarillas['time'],
                    y=alertas_amarillas['precip_acum_72h'],
                    mode='markers',
                    name='Alerta AMARILLA',
                    marker=dict(color='orange', size=8, symbol='circle')
                ),
                row=1, col=1
            )
    
    # Línea vertical en el presente - enfoque simple
    now = datetime.now()
    # Agregar como forma en lugar de vline para evitar problemas de conversión
    fig_lluvia.add_shape(
        type="line",
        x0=now, x1=now,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="green", width=2, dash="dot"),
        row=1, col=1
    )
    fig_lluvia.add_annotation(
        x=now,
        y=1,
        yref="paper",
        text="Ahora",
        showarrow=False,
        yshift=10,
        font=dict(color="green", size=12),
        row=1, col=1
    )
    
    # GRÁFICO 2: Evolución del nivel de alerta (área coloreada)
    # Mapear alertas a valores numéricos para el gráfico
    alerta_map = {'VERDE': 0, 'AMARILLA': 1, 'ROJA': 2}
    df_lluvia_torre['alerta_num'] = df_lluvia_torre['nivel_alerta_temporal'].map(alerta_map)
    
    # Crear áreas coloreadas por nivel de alerta
    color_alerta = {'VERDE': 'green', 'AMARILLA': 'orange', 'ROJA': 'red'}
    
    for nivel in ['VERDE', 'AMARILLA', 'ROJA']:
        df_nivel = df_lluvia_torre[df_lluvia_torre['nivel_alerta_temporal'] == nivel]
        if not df_nivel.empty:
            fig_lluvia.add_trace(
                go.Scatter(
                    x=df_nivel['time'],
                    y=[alerta_map[nivel]] * len(df_nivel),
                    mode='markers',
                    name=nivel,
                    marker=dict(
                        color=color_alerta[nivel],
                        size=8,
                        symbol='square'
                    ),
                    showlegend=False
                ),
                row=2, col=1
            )
    
    # Línea conectando los puntos
    fig_lluvia.add_trace(
        go.Scatter(
            x=df_lluvia_torre['time'],
            y=df_lluvia_torre['alerta_num'],
            mode='lines',
            line=dict(color='gray', width=1, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ),
        row=2, col=1
    )
    
    # Línea vertical en el presente (segunda gráfica)
    fig_lluvia.add_shape(
        type="line",
        x0=now, x1=now,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="green", width=2, dash="dot"),
        row=2, col=1
    )
    
    # Configurar ejes
    fig_lluvia.update_xaxes(title_text="Fecha y Hora", row=2, col=1)
    fig_lluvia.update_yaxes(title_text="Precipitación (mm)", row=1, col=1)
    fig_lluvia.update_yaxes(
        title_text="Nivel de Alerta",
        tickmode='array',
        tickvals=[0, 1, 2],
        ticktext=['🟢 VERDE', '🟡 AMARILLA', '🔴 ROJA'],
        row=2, col=1
    )
    
    fig_lluvia.update_layout(
        title_text=f"Evolución de Riesgo - {torre_seleccionada}",
        height=700,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig_lluvia, use_container_width=True)
    
    # Estadísticas del período
    col1, col2, col3 = st.columns(3)
    
    tiempo_roja = (df_lluvia_torre['nivel_alerta_temporal'] == 'ROJA').sum()
    tiempo_amarilla = (df_lluvia_torre['nivel_alerta_temporal'] == 'AMARILLA').sum()
    tiempo_verde = (df_lluvia_torre['nivel_alerta_temporal'] == 'VERDE').sum()
    total_horas = len(df_lluvia_torre)
    
    col1.metric(
        "🔴 Tiempo en Alerta Roja",
        f"{tiempo_roja} horas",
        delta=f"{tiempo_roja/total_horas*100:.1f}%"
    )
    col2.metric(
        "🟡 Tiempo en Alerta Amarilla",
        f"{tiempo_amarilla} horas",
        delta=f"{tiempo_amarilla/total_horas*100:.1f}%"
    )
    col3.metric(
        "🟢 Tiempo en Estado Normal",
        f"{tiempo_verde} horas",
        delta=f"{tiempo_verde/total_horas*100:.1f}%"
    )

# ============================================================================
# SECCIÓN 5: TABLA DE TORRES CON ALERTAS
# ============================================================================

st.markdown("---")
st.header("📋 Tabla de Torres Monitoreadas")

# Aplicar filtros
torres_filtradas = torres_df.copy()

if filtro_amenaza:
    torres_filtradas = torres_filtradas[torres_filtradas['Amenaza_SGC'].isin(filtro_amenaza)]

if filtro_riesgo:
    torres_filtradas = torres_filtradas[torres_filtradas['Clasificacion_Riesgo'].isin(filtro_riesgo)]

# Configurar colores
def colorear_alerta(val):
    color_dict = {
        'ROJA': 'background-color: #ffcccc',
        'AMARILLA': 'background-color: #fff4cc',
        'VERDE': 'background-color: #ccffcc'
    }
    return color_dict.get(val, '')

# Mostrar tabla
columnas_tabla = [
    'ID_Torre', 'Nombre', 'Amenaza_SGC', 'Pendiente_Grados', 
    'Lluvia_72h', 'Lluvia_24h', 'Clasificacion_Riesgo', 
    'Emoji_Alerta', 'Nivel_Alerta'
]

st.dataframe(
    torres_filtradas[columnas_tabla].style.applymap(
        colorear_alerta,
        subset=['Nivel_Alerta']
    ).format({
        'Pendiente_Grados': '{:.1f}°',
        'Lluvia_72h': '{:.1f}mm',
        'Lluvia_24h': '{:.1f}mm'
    }),
    use_container_width=True,
    hide_index=True,
    height=400
)

# Botón de descarga
csv = torres_filtradas.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar Datos como CSV",
    data=csv,
    file_name=f"torres_alertas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)

# ============================================================================
# SECCIÓN 6: ANÁLISIS DE HISTORIAL (SI EXISTE)
# ============================================================================

if not eventos_df.empty:
    st.markdown("---")
    st.header("📊 Análisis de Eventos Históricos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Eventos por torre
        eventos_por_torre = eventos_df['ID_Torre'].value_counts().head(10)
        
        fig_eventos = go.Figure(data=[
            go.Bar(
                x=eventos_por_torre.values,
                y=eventos_por_torre.index,
                orientation='h',
                marker_color='indianred'
            )
        ])
        
        fig_eventos.update_layout(
            title="Top 10 Torres con Más Eventos",
            xaxis_title="Número de Eventos",
            yaxis_title="Torre",
            height=400
        )
        
        st.plotly_chart(fig_eventos, use_container_width=True)
    
    with col2:
        # Distribución de magnitud
        magnitud_counts = eventos_df['Magnitud'].value_counts()
        
        fig_magnitud = go.Figure(data=[
            go.Pie(
                labels=magnitud_counts.index,
                values=magnitud_counts.values,
                marker_colors=['lightgreen', 'orange', 'red']
            )
        ])
        
        fig_magnitud.update_layout(
            title="Distribución de Magnitud de Eventos",
            height=400
        )
        
        st.plotly_chart(fig_magnitud, use_container_width=True)
    
    # Eventos en el tiempo
    eventos_tiempo = eventos_df.set_index('Fecha').resample('M').size()
    
    fig_tiempo = go.Figure(data=[
        go.Scatter(
            x=eventos_tiempo.index,
            y=eventos_tiempo.values,
            mode='lines+markers',
            line=dict(color='steelblue', width=2),
            marker=dict(size=8)
        )
    ])
    
    fig_tiempo.update_layout(
        title="Eventos de Deslizamiento en el Tiempo (Agrupados por Mes)",
        xaxis_title="Fecha",
        yaxis_title="Número de Eventos",
        height=300
    )
    
    st.plotly_chart(fig_tiempo, use_container_width=True)
    
    # Correlación precipitación vs eventos
    st.subheader("📈 Relación Precipitación vs Eventos")
    
    fig_correlacion = px.scatter(
        eventos_df,
        x='Precipitacion_72h_mm',
        y='Magnitud',
        color='Afecto_Infraestructura',
        size='Costo_Reparacion_USD',
        hover_data=['ID_Torre', 'Fecha'],
        title='Precipitación vs Magnitud del Evento',
        labels={
            'Precipitacion_72h_mm': 'Precipitación 72h (mm)',
            'Magnitud': 'Magnitud del Evento',
            'Afecto_Infraestructura': 'Afectó Infraestructura'
        }
    )
    
    fig_correlacion.update_layout(height=400)
    st.plotly_chart(fig_correlacion, use_container_width=True)

# ============================================================================
# SECCIÓN 7: ESTADÍSTICAS Y GRÁFICOS ADICIONALES
# ============================================================================

st.markdown("---")
st.header("📊 Estadísticas Adicionales")

tab1, tab2, tab3 = st.tabs(["🏔️ Amenaza", "📐 Pendiente", "🌧️ Precipitación"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de amenaza
        amenaza_counts = torres_df['Amenaza_SGC'].value_counts()
        
        fig_amenaza = go.Figure(data=[
            go.Bar(
                x=amenaza_counts.index,
                y=amenaza_counts.values,
                marker_color=['green', 'lightgreen', 'yellow', 'orange', 'red']
            )
        ])
        
        fig_amenaza.update_layout(
            title="Distribución de Niveles de Amenaza",
            xaxis_title="Nivel de Amenaza",
            yaxis_title="Número de Torres",
            height=400
        )
        
        st.plotly_chart(fig_amenaza, use_container_width=True)
    
    with col2:
        # Box plot de índice de riesgo por amenaza
        fig_box = px.box(
            torres_df,
            x='Amenaza_SGC',
            y='Indice_Riesgo',
            color='Amenaza_SGC',
            title='Índice de Riesgo por Nivel de Amenaza'
        )
        
        fig_box.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Histograma de pendientes
        fig_pendiente = px.histogram(
            torres_df,
            x='Pendiente_Grados',
            nbins=20,
            title='Distribución de Pendientes',
            labels={'Pendiente_Grados': 'Pendiente (grados)'}
        )
        
        fig_pendiente.update_layout(height=400)
        st.plotly_chart(fig_pendiente, use_container_width=True)
    
    with col2:
        # Scatter pendiente vs amenaza
        fig_scatter = px.scatter(
            torres_df,
            x='Pendiente_Grados',
            y='Indice_Riesgo',
            color='Amenaza_SGC',
            size='Lluvia_72h',
            title='Pendiente vs Índice de Riesgo',
            labels={
                'Pendiente_Grados': 'Pendiente (grados)',
                'Indice_Riesgo': 'Índice de Riesgo'
            }
        )
        
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de lluvia 72h
        fig_lluvia_dist = px.histogram(
            torres_df,
            x='Lluvia_72h',
            nbins=15,
            title='Distribución de Precipitación Acumulada (72h)',
            labels={'Lluvia_72h': 'Precipitación (mm)'}
        )
        
        fig_lluvia_dist.update_layout(height=400)
        st.plotly_chart(fig_lluvia_dist, use_container_width=True)
    
    with col2:
        # Top torres con más lluvia
        top_lluvia = torres_df.nlargest(10, 'Lluvia_72h')
        
        fig_top_lluvia = go.Figure(data=[
            go.Bar(
                x=top_lluvia['Lluvia_72h'],
                y=top_lluvia['ID_Torre'],
                orientation='h',
                marker_color='steelblue'
            )
        ])
        
        fig_top_lluvia.update_layout(
            title="Top 10 Torres con Mayor Precipitación",
            xaxis_title="Precipitación 72h (mm)",
            yaxis_title="Torre",
            height=400
        )
        
        st.plotly_chart(fig_top_lluvia, use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🛰️ Sistema de Alerta Temprana")
    st.caption("ISA INTERCOLOMBIA")

with col2:
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

with col3:
    st.caption("📊 Datos actualizados en tiempo real")
    st.caption("🌐 API: Open-Meteo")