# 🛰️ Sistema de Alerta Temprana de Deslizamientos

Prototipo de dashboard interactivo que combina datos de amenaza geoespacial y precipitación en tiempo real para generar alertas operacionales en torres de transmisión.

## 🎯 ¿Qué hace este proyecto?

Sistema que monitorea 15 torres en Arauca, Norte de Santander y Boyacá, generando 3 niveles de alerta:
- 🟢 **Verde**: Condiciones normales
- 🟡 **Amarilla**: Precaución - aumentar monitoreo  
- 🔴 **Roja**: Crítica - acción inmediata requerida

**Combina:**
1. Amenaza estática del terreno (clasificación SGC)
2. Pendiente del terreno
3. Precipitación en tiempo real (API Open-Meteo)

---

## ⚡ Inicio Rápido

### Requisitos
- Python 3.8+
- Git
- Conexión a Internet (para descargar dependencias y usar la API de lluvia)

### ⚙️ Instalación y Configuración

Para mantener las dependencias del proyecto aisladas y evitar conflictos, este repositorio incluye un entorno virtual (`venv`). Sigue los pasos correspondientes a tu sistema operativo.

---
#### 🔹 **Opción 1: macOS / Linux** (En la Terminal)
```bash
# 1. Clonar el repositorio y moverse a la carpeta
git clone [https://github.com/Pipe1017/isa-geospatial-alerts.git](https://github.com/Pipe1017/isa-geospatial-alerts.git)
cd isa-geospatial-alerts

# 2. Activar el entorno virtual
# (Notarás que la línea de comandos ahora empieza con "(venv)")
source venv/bin/activate

# 3. Instalar las dependencias requeridas
pip install -r requirements.txt

# 4. Navegar a la carpeta del dashboard y generar datos de prueba
cd dashboard
python simular_datos.py

# 5. Ejecutar el dashboard
streamlit run app.py

#### 🔹 Opción 2: Windows (En PowerShell o Command Prompt)

# 1. Clonar el repositorio y moverse a la carpeta
git clone [https://github.com/Pipe1017/isa-geospatial-alerts.git](https://github.com/Pipe1017/isa-geospatial-alerts.git)
cd isa-geospatial-alerts

# 2. Activar el entorno virtual
# (Notarás que la línea de comandos ahora empieza con "(venv)")
.\venv\Scripts\activate

# 3. Instalar las dependencias requeridas
pip install -r requirements.txt

# 4. Navegar a la carpeta del dashboard y generar datos de prueba
cd dashboard
python simular_datos.py

# 5. Ejecutar el dashboard
streamlit run app.py

---

## 📁 Estructura

```
isa-geospatial-alerts/
├── dashboard/
│   ├── app.py              # Dashboard Streamlit
│   └── simular_datos.py    # Genera datos de prueba
├── notebooks/
│   ├── 01-exploracion-tiff-amenaza.ipynb      # Análisis geoespacial
│   └── 02-analisis-torres-precipitacion.ipynb # Integración API
└── data/
    └── 03_external/        # CSVs generados automáticamente
```

---

## 🎨 Funcionalidades del Dashboard

- **Mapa interactivo** con alertas por torre
- **Matriz de riesgo** (Amenaza vs Precipitación)
- **Gráficos temporales** de evolución de riesgo
- **Tabla exportable** con todas las torres
- **Actualización en tiempo real** de datos de lluvia

---

## 📖 Matriz de Umbrales

| Amenaza | 🟡 Amarilla | 🔴 Roja |
|---------|-------------|---------|
| Muy Alta | > 80mm | > 100mm |
| Alta | > 100mm | > 120mm |
| Media | > 150mm | > 200mm |

*Precipitación acumulada en 72 horas*

---

## 🔧 Solución de Problemas

**Windows - "Python no se reconoce":**
```cmd
py -m pip install -r requirements.txt
py simular_datos.py
py -m streamlit run app.py
```

**"No se encontró archivo de torres":**
```bash
cd dashboard
python simular_datos.py
```

**"Port 8501 already in use":**
```bash
streamlit run app.py --server.port 8502
```

---

## 🛠️ Tecnologías

- **Streamlit** - Dashboard interactivo
- **Plotly** - Visualizaciones
- **Pandas/NumPy** - Análisis de datos
- **Rasterio** - Procesamiento geoespacial
- **Open-Meteo API** - Datos meteorológicos

---

## 📊 Notebooks

Análisis exploratorio en Jupyter:

1. **01-exploracion-tiff-amenaza.ipynb**  
   Lectura y clasificación de raster de amenaza (optimizado para archivos >100MB)

2. **02-analisis-torres-precipitacion.ipynb**  
   Integración con API de precipitación y cálculo de alertas

---

## 📝 Notas

- Datos simulados (prototipo para prueba técnica)
- API gratuita: ~10,000 llamadas/día
- Archivos `.tif` grandes excluidos del repositorio

---

## 👤 Autor

**Felipe Ruiz Zea**  
Candidato a Analista de Datos - Mantenimiento  
ISA INTERCOLOMBIA  
2025

---

## 📧 Contacto

GitHub: [@Pipe1017](https://github.com/Pipe1017)  
Repositorio: [isa-geospatial-alerts](https://github.com/Pipe1017/isa-geospatial-alerts)
