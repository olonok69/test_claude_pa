# Servidor MCP Yahoo Finance

Un servidor del Protocolo de Contexto de Modelo (MCP) que proporciona análisis integral de datos financieros e indicadores técnicos a través de la integración con Yahoo Finance. Este servidor permite que asistentes de IA y aplicaciones accedan a datos de mercado en tiempo real, realicen análisis técnico y generen señales de trading con algoritmos de puntuación propietarios avanzados.

## 🚀 Características

- **Datos de Mercado en Tiempo Real**: Acceso a precios actuales de acciones, volúmenes de trading e información de mercado
- **Herramientas de Análisis Técnico**: Indicadores avanzados incluyendo MACD, Bandas de Bollinger, Canales Donchian
- **Sistemas de Puntuación Personalizados**: Algoritmos propietarios para análisis técnico combinado
- **Generación de Señales de Trading**: Recomendaciones automatizadas de comprar/vender/mantener
- **Análisis de Portafolio**: Puntuación multi-indicador para decisiones de inversión
- **Compatible con MCP**: Implementa el Protocolo de Contexto de Modelo para integración con asistentes de IA

## 📋 Prerrequisitos

- Python 3.12+
- Docker (opcional, para despliegue contenerizado)
- Conexión a internet para acceso a datos de Yahoo Finance
- No se requieren claves API (usa datos públicos de Yahoo Finance)

## 🛠️ Instalación

### Configuración de Desarrollo Local

1. **Clonar el repositorio y navegar al directorio del servidor**:
   ```bash
   cd servers/server3
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el servidor**:
   ```bash
   python main.py
   ```

### Despliegue Docker

1. **Construir la imagen Docker**:
   ```bash
   docker build -t yahoo-finance-mcp-server .
   ```

2. **Ejecutar el contenedor**:
   ```bash
   docker run -p 8002:8002 yahoo-finance-mcp-server
   ```

## 🎯 Herramientas Disponibles

El servidor proporciona 6 poderosas herramientas de análisis financiero:

### 1. `calculate-macd-score-tool`
**Análisis Técnico MACD con Puntuación Personalizada**

- **Propósito**: Calcula una puntuación MACD integral (-100 a +100) combinando tres componentes
- **Componentes**:
  - Posición línea MACD vs línea Señal (40% peso)
  - Posición línea MACD vs línea Cero (30% peso)
  - Análisis momentum del histograma (30% peso)
- **Parámetros**:
  - `symbol`: Ticker de acción (ej., "AAPL", "TSLA")
  - `period`: Período de tiempo (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
  - `fast_period`: Período EMA rápido (por defecto: 12)
  - `slow_period`: Período EMA lento (por defecto: 26)
  - `signal_period`: Período EMA línea señal (por defecto: 9)

### 2. `calculate-donchian-channel-score-tool`
**Análisis de Canales Donchian con Puntuación Personalizada**

- **Propósito**: Calcula puntuación de Canales Donchian (-100 a +100) para análisis de tendencia y volatilidad
- **Componentes**:
  - Posición del precio dentro del canal (50% peso)
  - Tendencia de dirección del canal (30% peso)
  - Análisis de tendencia del ancho del canal (20% peso)
- **Parámetros**:
  - `symbol`: Ticker de acción
  - `period`: Período de tiempo
  - `window`: Período de lookback para cálculo del canal (por defecto: 20)

### 3. `calculate-combined-score-macd-donchian`
**Análisis Combinado Multi-Indicador**

- **Propósito**: Combina puntuaciones MACD y Donchian para señales de trading integrales
- **Señales de Trading**:
  - +75 a +100: Compra Fuerte
  - +50 a +75: Compra
  - +25 a +50: Compra Débil
  - -25 a +25: Neutral (Mantener)
  - -50 a -25: Venta Débil
  - -75 a -50: Venta
  - -100 a -75: Venta Fuerte
- **Parámetros**: Combina todos los parámetros MACD y Donchian

### 4. `calculate-bollinger-fibonacci-score`
**Estrategia Avanzada Bandas Bollinger + Retroceso Fibonacci**

- **Propósito**: Estrategia de trading sofisticada combinando Bandas de Bollinger con niveles Fibonacci
- **Componentes de Puntuación**:
  - Posición Bandas Bollinger (30% peso)
  - Evaluación de volatilidad (15% peso)
  - Interacción nivel Fibonacci (35% peso)
  - Análisis momentum precio (20% peso)
- **Parámetros**:
  - `ticker`: Ticker de acción
  - `period`: Período de tiempo
  - `window`: Período Bandas Bollinger (por defecto: 20)
  - `num_std`: Desviaciones estándar para bandas (por defecto: 2)
  - `window_swing_points`: Período detección puntos swing (por defecto: 10)
  - `fibonacci_levels`: Niveles retroceso Fibonacci
  - `num_days`: Número de días recientes a analizar (por defecto: 3)

### 5. `calculate-bollinger-z-score`
**Análisis Z-Score de Bollinger**

- **Propósito**: Calcula posición normalizada relativa a las Bandas de Bollinger
- **Interpretación**:
  - Z-Score > +2: Sobrecomprado (señal potencial de venta)
  - Z-Score < -2: Sobrevendido (señal potencial de compra)
  - Z-Score entre -2 y +2: Rango de trading normal
- **Parámetros**:
  - `symbol`: Ticker de acción
  - `period`: Período de cálculo (por defecto: 20)

### 6. `calculate-connors-rsi-score-tool` (Función Utilitaria)
**Análisis RSI Connors**

- **Propósito**: Cálculo RSI avanzado combinando RSI precio, RSI racha y rango porcentual
- **Componentes**:
  - RSI Precio (33.33% peso)
  - RSI Racha (33.33% peso)
  - Rango Porcentual (33.33% peso)

## 📊 Ejemplos de Uso

### Análisis Técnico Básico
```python
# Obtener análisis MACD para acciones Apple
{
  "symbol": "AAPL",
  "period": "1y",
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9
}
```

### Señal de Trading Combinada
```python
# Obtener señal de trading integral para Tesla
{
  "symbol": "TSLA",
  "period": "6mo",
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9,
  "window": 20
}
```

### Análisis de Estrategia Avanzada
```python
# Estrategia Bollinger-Fibonacci para Microsoft
{
  "ticker": "MSFT",
  "period": "1y",
  "window": 20,
  "num_std": 2,
  "window_swing_points": 10,
  "fibonacci_levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
  "num_days": 5
}
```

## 🔧 Endpoints API

### Herramientas MCP

El servidor expone herramientas de análisis financiero a través del protocolo MCP:

- **Descubrimiento de Herramientas**: Registro automático de todas las herramientas de análisis disponibles
- **Validación de Esquema**: Validación integral de entrada usando esquemas Zod
- **Manejo de Errores**: Gestión robusta de errores con retroalimentación detallada

### Endpoints HTTP

- **Verificación de Salud**: `GET /health` - Verificar estado del servidor
- **Endpoint SSE**: `GET /sse` - Server-Sent Events para comunicación MCP
- **Manejador de Mensajes**: `POST /messages/` - Manejar mensajes de protocolo MCP

## 🏗️ Arquitectura

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cliente MCP     │    │   Servidor       │    │   Yahoo Finance │
│                   │◄──►│   FastAPI        │◄──►│   API           │
│  - Solicitudes    │    │  - Registro      │    │  - Datos        │
│    Herramientas   │    │    Herramientas  │    │    Mercado      │
│  - Visualización  │    │  - Transporte    │    │  - Datos        │
│    Resultados     │    │    SSE           │    │    Históricos   │
│  - Manejo Errores │    │  - Validación    │    │                 │
└───────────────────┘    └──────────────────┘    └─────────────────┘
```

### Componentes Clave

- **`main.py`**: Servidor FastAPI con implementación de transporte SSE
- **`utils/yahoo_finance_tools.py`**: Algoritmos centrales de análisis financiero
- **Registro de Herramientas**: Sistema de auto-descubrimiento y registro de herramientas MCP
- **Capa de Validación**: Validación de entrada basada en Zod para todas las herramientas

## 🧮 Análisis Profundo de Indicadores Técnicos

### Algoritmo de Puntuación MACD

La puntuación MACD combina tres componentes ponderados:

1. **Cruce de Línea Señal (40%)**:
   - Mide la posición de la línea MACD relativa a la línea señal
   - Normalizado usando rango 3-sigma para consistencia

2. **Análisis de Línea Cero (30%)**:
   - Evalúa la posición de la línea MACD relativa a cero
   - Indica fortaleza de tendencia general

3. **Momentum del Histograma (30%)**:
   - Analiza tasa de cambio en el histograma MACD
   - Captura patrones de aceleración/desaceleración

### Puntuación de Canales Donchian

La puntuación Donchian evalúa tres aspectos:

1. **Posición del Canal (50%)**:
   - Ubicación del precio dentro de los límites del canal
   - Escalado lineal desde banda inferior (-50) a banda superior (+50)

2. **Dirección del Canal (30%)**:
   - Análisis de tendencia del punto medio del canal
   - Cambio direccional suavizado de 5 días

3. **Evaluación de Volatilidad (20%)**:
   - Análisis de expansión/contracción del ancho del canal
   - Indica cambios en volatilidad del mercado

### Integración Bollinger-Fibonacci

Estrategia avanzada combinando:

1. **Posición %B**: Posición porcentual de Bandas Bollinger
2. **Métricas de Volatilidad**: Ancho de banda y análisis de expansión
3. **Interacciones Fibonacci**: Proximidad del precio a niveles de retroceso clave
4. **Indicadores de Momentum**: Evaluación de momentum basada en RSI

## 🔍 Manejo de Errores

El servidor incluye manejo integral de errores:

- **Validación de Datos**: Validación de parámetros de entrada y verificación de tipos
- **Errores de API**: Gestión de errores de API Yahoo Finance y lógica de reintentos
- **Errores de Cálculo**: Manejo de errores de operaciones matemáticas
- **Datos Faltantes**: Manejo elegante de datos históricos insuficientes

## 📈 Consideraciones de Rendimiento

- **Caché de Datos**: Caché eficiente de símbolos solicitados frecuentemente
- **Procesamiento por Lotes**: Cálculos optimizados para múltiples indicadores
- **Gestión de Memoria**: Operaciones eficientes de DataFrame pandas
- **Limitación de Tasa API**: Uso respetuoso de la API Yahoo Finance

## 🐛 Solución de Problemas

### Problemas Comunes

**Símbolo No Encontrado**:
- Verificar formato de símbolo ticker (ej., "AAPL" no "Apple")
- Verificar si el símbolo existe en Yahoo Finance
- Usar sufijos de intercambio correctos para acciones internacionales

**Datos Insuficientes**:
- Reducir requisitos de período de análisis
- Verificar si el símbolo tiene suficiente historial de trading
- Verificar horarios de mercado y disponibilidad de datos

**Errores de Cálculo**:
- Asegurar que se cumplan los requisitos mínimos de datos
- Verificar acciones corporativas que afecten datos de precios
- Verificar que los rangos de parámetros estén dentro de límites válidos

### Modo Debug

Habilitar logging detallado estableciendo nivel de log en `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔗 Integración con Asistentes de IA

Este servidor implementa el Protocolo de Contexto de Modelo (MCP), haciéndolo compatible con:
- Claude Desktop
- Otros asistentes de IA compatibles con MCP
- Aplicaciones personalizadas usando clientes MCP

### Configuración Cliente MCP

Agregar a la configuración de tu cliente MCP:
```json
{
  "mcpServers": {
    "yahoo-finance": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/ruta/a/servers/server3"
    }
  }
}
```

## 💡 Casos de Uso

### Gestión de Portafolio
- Analizar múltiples acciones simultáneamente
- Generar señales técnicas combinadas
- Rastrear momentum a través de diferentes marcos temporales

### Desarrollo de Estrategias de Trading
- Hacer backtest de combinaciones de indicadores
- Evaluar precisión y timing de señales
- Desarrollar metodologías de puntuación personalizadas

### Investigación de Mercado
- Análisis sectorial usando múltiples indicadores
- Análisis técnico comparativo
- Identificación y validación de tendencias

### Aplicaciones Educativas
- Aprender conceptos de análisis técnico
- Entender interacciones de indicadores
- Practicar interpretación de señales

## 🔄 Mejoras Futuras

- **Indicadores Adicionales**: RSI, Estocástico, Williams %R
- **Análisis Sectorial**: Análisis técnico a nivel de industria
- **Datos de Opciones**: Análisis de volatilidad y flujo de opciones
- **Indicadores Económicos**: Integración con datos económicos
- **Streaming en Tiempo Real**: Actualizaciones de datos de mercado en vivo

---

**Versión**: 1.0.0  
**Compatible con**: Python 3.12+, FastAPI 0.104+, MCP 1.6.0+, yfinance 0.2.61+