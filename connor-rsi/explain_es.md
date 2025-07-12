# Documentación del Indicador Connors RSI

## Índice
1. [¿Qué es el Connors RSI?](#qué-es-el-connors-rsi)
2. [Los 3 Componentes del Connors RSI](#los-3-componentes-del-connors-rsi)
3. [Cálculo del Connors RSI Final](#cálculo-del-connors-rsi-final)
4. [Interpretación de los Niveles](#interpretación-de-los-niveles)
5. [Ejemplo Práctico](#ejemplo-práctico-de-interpretación)
6. [Ventajas sobre el RSI Tradicional](#ventajas-del-connors-rsi-sobre-rsi-tradicional)
7. [Estrategias de Trading](#estrategia-de-trading-típica)
8. [Limitaciones y Consideraciones](#limitaciones-y-consideraciones)
9. [Innovaciones en Nuestro Código](#innovación-en-nuestro-código)

---

## ¿Qué es el Connors RSI?

El **Connors RSI (CRSI)** es un indicador técnico desarrollado por **Larry Connors** que combina tres componentes diferentes para identificar condiciones de sobrecompra y sobreventa con mayor precisión que el RSI tradicional. Es especialmente efectivo para estrategias de **reversión a la media** en marcos temporales cortos.

### Características Principales:
- ✅ **Más preciso** que el RSI tradicional
- ✅ **Menos señales falsas**
- ✅ **Mejor timing** para entradas y salidas
- ✅ **Combina tres perspectivas** del momentum

---
### RSI tradicional
El RSI (Relative Strength Index o Índice de Fuerza Relativa) es uno de los indicadores técnicos más populares en trading. Fue desarrollado por J. Welles Wilder Jr. en 1978 y es un oscilador de momentum que mide la velocidad y magnitud de los cambios de precio.

#### ¿Qué mide el RSI?

El RSI evalúa si un activo está sobrecomprado o sobrevendido, oscilando entre 0 y 100. Tradicionalmente:
- **RSI > 70**: Zona de sobrecompra (posible señal de venta)
- **RSI < 30**: Zona de sobreventa (posible señal de compra)
- **RSI entre 30-70**: Zona neutral

#### Cálculo del RSI

El RSI se calcula en varios pasos:

##### Paso 1: Calcular los cambios de precio
Para cada período, se calcula la diferencia entre el precio de cierre actual y el anterior.

##### Paso 2: Separar ganancias y pérdidas
- **Ganancia**: Si el cambio es positivo
- **Pérdida**: Si el cambio es negativo (se toma el valor absoluto)

##### Paso 3: Calcular promedios
Se calculan las medias móviles de las ganancias y pérdidas, típicamente usando 14 períodos:
- **Promedio de Ganancias (AG)**: Media de las ganancias en n períodos
- **Promedio de Pérdidas (AP)**: Media de las pérdidas en n períodos

##### Paso 4: Calcular RS (Relative Strength)
RS = Promedio de Ganancias / Promedio de Pérdidas

##### Paso 5: Calcular RSI
RSI = 100 - (100 / (1 + RS))

#### Interpretación práctica

El RSI es útil para:
- Identificar condiciones de sobrecompra/sobreventa
- Detectar divergencias con el precio
- Confirmar tendencias
- Generar señales de entrada y salida



## Los 3 Componentes del Connors RSI

### 1. RSI de Precios (33.33% del peso)

```python
# RSI tradicional pero con período corto (3 días por defecto)
price_rsi = rsi(close, rsi_period=3)
```

**¿Qué mide?** 
El momentum tradicional de los precios de cierre

**Interpretación:**
- `RSI > 50`: Momentum alcista
- `RSI < 50`: Momentum bajista
- Usa un período más corto (3) que el RSI tradicional (14) para ser más sensible

---

### 2. RSI de Rachas (33.33% del peso)

```python
streak_rsi_values = streak_rsi(close, streak_period=2)
```

**¿Qué mide?** 
La persistencia de movimientos consecutivos al alza o a la baja

**Cómo funciona:**
- Cuenta días consecutivos de subidas (+1, +2, +3...)
- Cuenta días consecutivos de bajadas (-1, -2, -3...)
- Aplica RSI a esta serie de rachas

**Ejemplo práctico:**
```
Precios: 100 → 101 → 102 → 101 → 100 → 99
Rachas:   0 →  +1 →  +2 →  -1 →  -2 → -3
```

**Interpretación:**
- **RSI de rachas alto**: Ha habido muchas rachas alcistas recientemente
- **RSI de rachas bajo**: Ha habido muchas rachas bajistas recientemente

---

### 3. Rango Percentil (33.33% del peso)

```python
roc = close.pct_change() * 100  # Tasa de cambio porcentual
percent_rank_values = percent_rank(roc, rank_period=100)
```

**¿Qué mide?** 
En qué percentil se encuentra el cambio de precio actual comparado con los últimos 100 días

**Interpretación:**
- **Percentil 90**: El cambio de hoy está entre el 10% más alto de los últimos 100 días
- **Percentil 10**: El cambio de hoy está entre el 10% más bajo de los últimos 100 días

---

## Cálculo del Connors RSI Final

```python
# 1. Promedio simple de los tres componentes
crsi = (price_rsi + streak_rsi_values + percent_rank_values) / 3

# 2. Conversión a escala de puntaje (-100 a +100)
connors_score = (crsi - 50) * 2
```

### Fórmula Matemática:
```
CRSI = (RSI_Precio + RSI_Rachas + Rango_Percentil) ÷ 3
```

---

## Interpretación de los Niveles

### Niveles Tradicionales del CRSI (0-100):
| Rango | Condición | Señal |
|-------|-----------|-------|
| **< 20** | **Sobreventa extrema** | 🟢 Señal de compra potencial |
| **20-80** | Rango normal | ⚪ Sin señales claras |
| **> 80** | **Sobrecompra extrema** | 🔴 Señal de venta potencial |

### Nuestro Sistema de Puntuación (-100 a +100):

```python
if score > 75:      # 🟢 "Strong Buy Signal"
elif score > 50:    # 🟢 "Buy Signal" 
elif score > 25:    # 🟡 "Weak Buy Signal"
elif score > -25:   # ⚪ "Neutral"
elif score > -50:   # 🟡 "Weak Sell Signal"
elif score > -75:   # 🔴 "Sell Signal"
else:               # 🔴 "Strong Sell Signal"
```

| Rango de Score | Señal | Descripción |
|----------------|-------|-------------|
| **+75 a +100** | 🟢 **Strong Buy** | Condiciones muy favorables para compra |
| **+50 a +75** | 🟢 **Buy** | Condiciones favorables para compra |
| **+25 a +50** | 🟡 **Weak Buy** | Ligera inclinación alcista |
| **-25 a +25** | ⚪ **Neutral** | Sin señales claras, mantener posición |
| **-50 a -25** | 🟡 **Weak Sell** | Ligera inclinación bajista |
| **-75 a -50** | 🔴 **Sell** | Condiciones favorables para venta |
| **-100 a -75** | 🔴 **Strong Sell** | Condiciones muy favorables para venta |

---

## Ejemplo Práctico de Interpretación

### Resultado del Análisis:
```
Symbol: AAPL, Period: 1y
Latest Connors RSI: 15.30
Latest Connors RSI Score: -69.40

Component Analysis:
1. Price RSI (33.33% weight): 25.50 -> Score: -16.33
2. Streak RSI (33.33% weight): 12.10 -> Score: -25.27
3. Percent Rank (33.33% weight): 8.30 -> Score: -27.80

Market Condition: Oversold (Potential Buy Signal)
```

### Interpretación Detallada:

1. **Price RSI (25.50)**: 
   - El momentum de precios está bajo
   - Indica presión vendedora reciente

2. **Streak RSI (12.10)**: 
   - Ha habido muchas rachas bajistas consecutivas
   - Sugiere que la tendencia bajista está perdiendo fuerza

3. **Percent Rank (8.30)**: 
   - Los cambios de precio actuales están en el 8% inferior de los últimos 100 días
   - El movimiento bajista actual es estadísticamente significativo

4. **CRSI Final (15.30)**: 
   - Condición de **sobreventa extrema**
   - Alta probabilidad de reversión al alza

5. **Score (-69.40)**: 
   - Señal de **"Sell"** pero muy cerca de **"Strong Sell"**
   - Momento óptimo para considerar una posición larga

---

## Ventajas del Connors RSI sobre RSI Tradicional

### 1. 🎯 Menos Señales Falsas
- **Problema del RSI tradicional**: Puede dar señales prematuras en tendencias fuertes
- **Solución del Connors RSI**: Combina tres perspectivas diferentes del momentum
- **Resultado**: Reduce significativamente la probabilidad de señales erróneas

### 2. ⏰ Mejor Timing
- **Componente de rachas**: Ayuda a identificar cuando una tendencia está perdiendo fuerza
- **Rango percentil**: Proporciona contexto histórico para el timing
- **Resultado**: Entradas y salidas más precisas

### 3. 🔄 Más Sensible a Cambios
- **Períodos más cortos**: Usa RSI de 3 períodos vs. 14 tradicional
- **Detección temprana**: Identifica reversiones antes que el RSI tradicional
- **Resultado**: Oportunidades de trading más tempranas

### 4. 📊 Análisis Multidimensional
| Aspecto | RSI Tradicional | Connors RSI |
|---------|-----------------|-------------|
| **Componentes** | 1 (solo precio) | 3 (precio + rachas + percentil) |
| **Sensibilidad** | Media | Alta |
| **Señales Falsas** | Más frecuentes | Menos frecuentes |
| **Contexto Histórico** | Limitado | Completo |

---

## Estrategia de Trading Típica

### 🟢 Señales de Compra

**Condiciones Ideales:**
- ✅ `CRSI < 20` (especialmente < 10)
- ✅ Los tres componentes deben estar bajos
- ✅ Esperar confirmación con incremento del CRSI

**Ejemplo de Setup de Compra:**
```
CRSI: 12.5 (sobreventa extrema)
Price RSI: 18.2 (bajo)
Streak RSI: 8.1 (muchas rachas bajistas)
Percent Rank: 11.2 (movimiento en percentil bajo)
```

### 🔴 Señales de Venta

**Condiciones Ideales:**
- ✅ `CRSI > 80` (especialmente > 90)
- ✅ Los tres componentes deben estar altos
- ✅ Esperar confirmación con disminución del CRSI

**Ejemplo de Setup de Venta:**
```
CRSI: 87.3 (sobrecompra extrema)
Price RSI: 89.1 (alto)
Streak RSI: 91.2 (muchas rachas alcistas)
Percent Rank: 81.6 (movimiento en percentil alto)
```

### 🛡️ Gestión de Riesgo

```python
# Combinación con Z-Score para mayor confirmación
if current_crsi < 20 and current_zscore < -1:
    # Sobreventa + precio estadísticamente bajo = Oportunidad de compra fuerte
    signal = "STRONG BUY"
    
elif current_crsi > 80 and current_zscore > 1:
    # Sobrecompra + precio estadísticamente alto = Oportunidad de venta fuerte
    signal = "STRONG SELL"
```

### 📋 Reglas de Trading Recomendadas

1. **Entrada**: 
   - Compra cuando CRSI < 20
   - Venta cuando CRSI > 80

2. **Confirmación**:
   - Esperar que al menos 2 de los 3 componentes confirmen la señal
   - Usar stop-loss del 2-3% desde el punto de entrada

3. **Salida**:
   - Cerrar longs cuando CRSI > 70
   - Cerrar shorts cuando CRSI < 30

4. **Filtros adicionales**:
   - Confirmar con análisis de volumen
   - Verificar soporte/resistencia técnica
   - Considerar el contexto del mercado general

---

## Limitaciones y Consideraciones

### ⚠️ 1. Mejor en Mercados Laterales
- **Funciona mejor**: Cuando los precios oscilan en rangos definidos
- **Problema**: En tendencias fuertes puede dar señales prematuras
- **Solución**: Combinar con análisis de tendencia

### ⚠️ 2. Requiere Confirmación
- **No usar como único indicador**
- **Combinar con**: 
  - Análisis de tendencia
  - Indicadores de volumen
  - Soportes y resistencias
  - Análisis fundamental

### ⚠️ 3. Dependiente del Timeframe
- **Optimizado**: Para trading de corto plazo (intraday a semanal)
- **Precaución**: Para inversiones de largo plazo
- **Recomendación**: Ajustar parámetros según el timeframe

### ⚠️ 4. Sensibilidad a Parámetros
- **Parámetros estándar**: RSI(3), Streak(2), PercentRank(100)
- **Optimización**: Puede requerir ajustes según el activo
- **Backtesting**: Esencial antes de usar en trading real

---

## Innovación en Nuestro Código

### 🚀 Mejoras Implementadas

#### 1. **Combinación con Z-Score**
```python
# Análisis de reversión a la media mejorado
zscore_analysis = calculate_zscore_indicator(symbol, period, window=20)
combined_score = (connors_score * 0.7) + (zscore_score * 0.3)
```

**Beneficios:**
- Confirmación estadística adicional
- Mejor identificación de extremos de precio
- Reducción de señales falsas

#### 2. **Sistema de Puntuación Unificado (-100 a +100)**
```python
# Conversión intuitiva
connors_score = (crsi - 50) * 2

# Interpretación uniforme
if score > 75: return "Strong Buy Signal"
```

**Beneficios:**
- Fácil comparación entre diferentes indicadores
- Interpretación más intuitiva
- Integración simple con otros sistemas

#### 3. **Análisis Detallado de Componentes**
```python
message = f"""
Component Analysis:
1. Price RSI (33.33% weight): {current_price_rsi:.2f} -> Score: {price_rsi_score:.2f}
2. Streak RSI (33.33% weight): {current_streak_rsi:.2f} -> Score: {streak_rsi_score:.2f}
3. Percent Rank (33.33% weight): {current_percent_rank:.2f} -> Score: {percent_rank_score:.2f}
"""
```

**Beneficios:**
- Transparencia total en el cálculo
- Identificación de componentes débiles/fuertes
- Mejor comprensión de las señales

#### 4. **Integración con Otras Estrategias**
- **MACD + Donchian**: Para análisis de momentum y canales
- **Bollinger Bands + Fibonacci**: Para análisis técnico avanzado
- **Múltiples timeframes**: Análisis desde intraday hasta anual

### 🛠️ Funcionalidades Técnicas

#### MCP Tools Disponibles:
1. `calculate_connors_rsi_score_tool()` - Análisis completo de Connors RSI
2. `calculate_zscore_indicator_tool()` - Análisis de Z-Score
3. `calculate_combined_connors_zscore_tool()` - Análisis combinado

#### Parámetros Configurables:
- `rsi_period`: Período para RSI de precios (default: 3)
- `streak_period`: Período para RSI de rachas (default: 2)
- `rank_period`: Período para rango percentil (default: 100)
- `zscore_window`: Ventana para Z-Score (default: 20)
- `connors_weight`: Peso del Connors RSI (default: 0.7)
- `zscore_weight`: Peso del Z-Score (default: 0.3)

---

## Conclusión

El **Connors RSI** representa una evolución significativa del RSI tradicional, ofreciendo:

✅ **Mayor precisión** en la identificación de extremos de mercado  
✅ **Menos señales falsas** gracias a su análisis multidimensional  
✅ **Mejor timing** para entradas y salidas  
✅ **Flexibilidad** para diferentes estrategias de trading  

Nuestra implementación mejora aún más el indicador original al combinarlo con análisis estadístico (Z-Score) y proporcionar un sistema de puntuación uniforme que facilita la toma de decisiones de trading.

**Recomendación**: Usar el Connors RSI como parte de un sistema de trading diversificado, siempre con gestión de riesgo adecuada y confirmación de múltiples indicadores.

---

