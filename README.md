# 🛰️ Sistema de Alerta Temprana de Deslizamientos - ISA

Dashboard interactivo para monitoreo de torres de transmisión que combina amenaza estática, pendiente del terreno y precipitación en tiempo real.

## 🚀 Inicio Rápido

### Requisitos
- Python 3.8 o superior
- Conexión a internet (para API de precipitación)

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/Pipe1017/isa-geospatial-alerts.git
cd isa-geospatial-alerts

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Generar datos de prueba
cd dashboard
python simular_datos.py

# 5. Ejecutar aplicación
streamlit run app.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📊 Componentes del Proyecto

### 1. Notebooks de Análisis

#### `notebooks/01-exploracion-tiff-amenaza.ipynb`
- Lectura optimizada de archivos TIFF grandes (sin saturar RAM)
- Procesamiento por bloques
- Extracción de región específica (Arauca, Norte de Santander, Boyacá)
- Clasificación de amenaza en 3 niveles: Baja, Media, Alta
- Análisis estadístico completo

#### `notebooks/02-analisis-torres-precipitacion.ipynb`
- Integración con Open-Meteo API para datos de precipitación
- Extracción de valores de amenaza por coordenadas de torres
- Cálculo de nivel de alerta según matriz de riesgo
- Visualizaciones interactivas con Plotly
- Análisis temporal de riesgo

### 2. Dashboard Streamlit

**Archivo**: `dashboard/app.py`

**Funcionalidades principales:**
- ✅ Monitoreo en tiempo real de 15 torres
- ✅ Mapa interactivo con marcadores de alerta
- ✅ Matriz de riesgo (Amenaza vs Precipitación)
- ✅ Gráficos de evolución temporal por torre
- ✅ Sistema de 3 niveles de alerta: 🟢 Verde, 🟡 Amarilla, 🔴 Roja
- ✅ Análisis detallado por torre
- ✅ Tabla completa con filtros
- ✅ Exportación de datos a CSV

**Navegación:**
1. **Sidebar**: Seleccionar torre y actualizar datos
2. **Resumen Ejecutivo**: Métricas clave del sistema
3. **Mapa Interactivo**: Vista geográfica de alertas
4. **Matriz de Riesgo**: Scatter plot interactivo
5. **Análisis Detallado**: Evolución temporal de riesgo
6. **Tabla de Torres**: Datos completos exportables

### 3. Generador de Datos

**Archivo**: `dashboard/simular_datos.py`

Genera datos simulados basados en clasificación del Servicio Geológico Colombiano (SGC):
- Ubicación y características de 15 torres
- Niveles de amenaza (Muy Baja, Baja, Media, Alta, Muy Alta)
- Pendientes del terreno
- Historial de eventos
- Matriz de umbrales de lluvia

## 🌐 Fuentes de Datos

### Amenaza Estática
- **Fuente**: Simulada según clasificación SGC
- **Niveles**: Muy Baja, Baja, Media, Alta, Muy Alta
- **Método**: Clasificación por percentiles (P33, P66)

### Precipitación en Tiempo Real
- **API**: Open-Meteo (https://open-meteo.com)
- **Datos**: Históricos y pronóstico de 7 días
- **Frecuencia**: Actualización horaria
- **Ventana**: Acumulado de 72 horas

### Ubicación de Torres
- **Región**: Arauca, Norte de Santander, Boyacá
- **Total**: 15 torres de transmisión
- **Coordenadas**: Latitud/Longitud en WGS84

## 📖 Matriz de Riesgo

### Umbrales de Alerta por Nivel de Amenaza

| Amenaza    | 🟡 Alerta Amarilla | 🔴 Alerta Roja |
|------------|-------------------|----------------|
| Muy Alta   | > 80mm            | > 100mm        |
| Alta       | > 100mm           | > 120mm        |
| Media      | > 150mm           | > 200mm        |
| Baja       | > 200mm           | > 250mm        |
| Muy Baja   | > 250mm           | > 300mm        |

*Precipitación acumulada en 72 horas*

### Índice de Riesgo Compuesto

El sistema calcula un índice de riesgo (0-100) combinando:
- **Amenaza estática** (15%)
- **Pendiente del terreno** (25%)
- **Historial de eventos** (20%)
- **Distancia a drenajes** (15%)
- **Factores adicionales** (25%)

**Clasificación:**
- 🟢 Riesgo Bajo: < 30
- 🟡 Riesgo Medio: 30-60
- 🔴 Riesgo Alto: > 60

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**
- **Streamlit** - Framework para dashboard interactivo
- **Plotly** - Visualizaciones interactivas
- **Pandas & NumPy** - Análisis y manipulación de datos
- **Rasterio** - Procesamiento de datos geoespaciales
- **Requests** - Integración con APIs
- **Open-Meteo API** - Datos meteorológicos

## 📂 Estructura del Proyecto

```
isa-geospatial-alerts/
│
├── README.md                              # Este archivo
├── requirements.txt                       # Dependencias Python
├── .gitignore                            # Archivos excluidos de Git
│
├── notebooks/                            # Análisis exploratorio
│   ├── 01-exploracion-tiff-amenaza.ipynb
│   └── 02-analisis-torres-precipitacion.ipynb
│
├── dashboard/                            # Aplicación web
│   ├── app.py                           # Dashboard Streamlit
│   └── simular_datos.py                 # Generador de datos
│
└── data/                                # Datos del proyecto
    └── 03_external/                     # Datos generados
        ├── ubicacion_torres.csv
        ├── ubicacion_torres_completo.csv
        ├── historial_eventos.csv
        └── umbrales_lluvia.csv
```

## 📸 Capturas de Pantalla

Para tomar capturas del dashboard:
- **Mac**: `Cmd + Shift + 4`
- **Windows**: `Win + Shift + S`
- **Desde gráficos Plotly**: Hover sobre el gráfico → Click en icono 📷

## 🐛 Solución de Problemas

### Error: "No se encontró el archivo de torres"
```bash
cd dashboard
python simular_datos.py
```

### Error: "Port 8501 already in use"
```bash
streamlit run app.py --server.port 8502
```

### Error al instalar rasterio

**En Mac:**
```bash
brew install gdal
pip install rasterio
```

**En Ubuntu/Debian:**
```bash
sudo apt-get install gdal-bin libgdal-dev
pip install rasterio
```

**En Windows:**
```bash
# Usar conda (más fácil)
conda install -c conda-forge rasterio
```

## 🔄 Actualización de Datos

El dashboard actualiza automáticamente los datos de precipitación:
- **Cache**: 1 hora
- **Actualización manual**: Botón "🔄 Actualizar Datos" en el sidebar
- **Límite API**: ~10,000 llamadas/día (Open-Meteo gratuito)

## 📝 Notas Importantes

### Datos Simulados
Este es un **prototipo** con datos simulados. Para producción:
- Integrar con datos reales del Servicio Geológico Colombiano (SGC)
- Conectar con sistemas de monitoreo de ISA
- Validar umbrales con histórico de eventos reales
- Implementar sistema de notificaciones automáticas

### Archivos Grandes
Los archivos raster `.tif` (>100MB) no están incluidos en el repositorio por su tamaño. Para trabajar con datos reales:
1. Obtener raster de amenaza del SGC
2. Colocarlo en `data/01_raw/`
3. Ejecutar notebooks para procesamiento

## 👥 Autor

**Felipe Ruiz**  
Sistema de Alerta Temprana de Deslizamientos  
2025

---

**Versión**: 1.0  
**Última actualización**: Enero 2025
git
