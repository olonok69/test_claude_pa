## Transportes de Servidor del Protocolo de Contexto de Modelo (MCP)

El Protocolo de Contexto de Modelo (MCP) es un estándar abierto que
permite a las aplicaciones de IA conectarse con herramientas externas,
fuentes de datos y servicios. MCP admite diferentes mecanismos de
transporte para la comunicación entre clientes y servidores, siendo
**stdio** y **SSE (Eventos Enviados por el Servidor)** las dos
opciones principales.

## Descripción General de Transportes

MCP incluye dos implementaciones de transporte estándar: El transporte
stdio permite la comunicación a través de flujos de entrada y salida
estándar, particularmente útil para integraciones locales y
herramientas de línea de comandos. El transporte SSE permite streaming
del servidor al cliente con solicitudes HTTP POST para la comunicación
del cliente al servidor.

Ambos transportes utilizan JSON-RPC 2.0 como el formato de mensaje
subyacente para la comunicación.

## Transporte STDIO

### Qué es:
El transporte STDIO se ejecuta localmente en tu máquina y se comunica
a través de flujos de entrada/salida estándar. El cliente genera un
servidor MCP como un proceso hijo.

### Características Clave:
**Ejecución Local**: Este transporte lanza el servidor como un proceso
hijo y se comunica a través de flujos de entrada y salida estándar. Es
ideal para integraciones locales y herramientas de línea de comandos.

**Comunicación de Procesos**: La comunicación ocurre a través de
flujos de procesos: el cliente escribe al STDIN del servidor, el
servidor responde al STDOUT

**Seguridad**: Más seguro por defecto ya que la comunicación permanece
dentro de la máquina local

**Despliegue**: El ejecutable del servidor debe estar instalado en la
máquina de cada usuario

### Ejemplo de Configuración:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./server.js"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

### Ventajas:
- Simple de implementar y depurar
- Seguro (sin exposición de red)
- Comunicación directa de procesos
- Menor latencia
- La especificación oficial de MCP recomienda que los clientes admitan
stdio siempre que sea posible

### Limitaciones:
- Relación uno a uno cliente-servidor
- Tanto el cliente como el servidor deben ejecutarse en la misma máquina
- Sin capacidad de acceso a la red
- Escalabilidad limitada

## Transporte SSE (Eventos Enviados por el Servidor)

### Qué es:
Funciona sobre HTTP estándar (no se necesitan protocolos especiales),
mantiene una conexión persistente para mensajes del servidor al
cliente, y puede usar mecanismos de autenticación HTTP estándar.

### Características Clave:
**Basado en Red**: Puede ejecutarse en diferentes máquinas a través de redes

**Basado en HTTP**: Utiliza solicitudes HTTP POST para la comunicación
cliente-servidor y Eventos Enviados por el Servidor para streaming
servidor-cliente.

**Acceso Remoto**: Permite despliegues distribuidos

**Autenticación**: Admite mecanismos de autenticación HTTP estándar

### Ejemplo de Configuración:
```json
{
  "mcpServers": {
    "remote-server": {
      "type": "sse",
      "url": "https://emea01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fapi.example.com%2Fsse&data=05%7C02%7C%7C7882db5f92624177b2bb08dd9aa5dcb8%7C84df9e7fe9f640afb435aaaaaaaaaaaa%7C1%7C0%7C638836759330805868%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=to9qooAS9ECO0pkAMs0zbOAlRBwWHc68i5V1MPFKukE%3D&reserved=0",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

### Ventajas:
- Puede servir múltiples clientes simultáneamente
- Permite despliegues remotos/distribuidos
- Funciona a través de redes
- Admite autenticación y autorización
- Mejor para soluciones basadas en la nube
- Puede exponerse a través de URLs para un acceso más amplio

### Limitaciones:
**Consideraciones de Seguridad**: Los transportes SSE pueden ser
vulnerables a ataques de DNS rebinding si no están adecuadamente
asegurados. Para prevenir esto: Siempre valida los encabezados Origin
en las conexiones SSE entrantes, evita vincular servidores a todas las
interfaces de red (0.0.0.0) cuando se ejecute localmente, e implementa
autenticación adecuada para todas las conexiones SSE.

- Más complejo de implementar
- Requiere configuración de red
- Vulnerabilidades de seguridad potenciales si no está configurado adecuadamente
- Mayor latencia comparado con stdio

## Cuándo Elegir Qué Transporte

### Elige STDIO cuando:
- Construyas herramientas de desarrollo locales
- Crees integraciones simples de línea de comandos
- La seguridad sea una preocupación principal
- Escenarios de usuario único
- Se necesite acceso al sistema de archivos local
- Trabajes con herramientas de línea de comandos que requieren
comunicación directa entre procesos en la misma máquina

### Elige SSE cuando:
- Construyas aplicaciones basadas en web
- Necesites servir múltiples clientes
- Se requiera despliegue de servidor remoto
- Soluciones basadas en la nube
- Se necesite autenticación/autorización
- La compatibilidad multiplataforma sea importante
- Trabajes en entornos distribuidos donde clientes y servidores están
separados a través de diferentes sistemas o redes

## Soporte Actual del Ecosistema

**Soporte de Cliente**: En este momento, Claude Desktop no admite SSE,
aunque hay soluciones proxy disponibles.

**Soluciones de la Comunidad**: Muchos servidores MCP de la comunidad
solo implementan transporte stdio, que típicamente es inaccesible para
asistentes remotos. Herramientas como Supergateway han sido
desarrolladas como utilidades de código abierto que convierten
servidores MCP stdio a SSE.

## Resumen

La elección entre stdio y SSE finalmente depende de tu caso de uso
específico, requisitos de despliegue y consideraciones de seguridad.
STDIO es preferido por simplicidad y desarrollo local, mientras que
SSE es más adecuado para escenarios distribuidos de múltiples
clientes.