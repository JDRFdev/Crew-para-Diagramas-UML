# Crew para Diagramas UML

Este proyecto utiliza CrewAI para automatizar la creacion de diagramas UML a partir de una descripcion tecnica. El sistema utiliza un flujo (Flow) de dos cuadrillas (Crews) especializadas y herramientas personalizadas de Python para la integracion con servicios externos.

## Que hace este proyecto?

1.  Crew de Analisis: Lee una descripcion del sistema (desde system.txt), analiza la problematica y define que diagramas UML son necesarios (Clases, Secuencia, etc.).
2.  Crew de Desarrollo: Toma el analisis, genera el codigo PlantUML y utiliza una herramienta personalizada (Custom Tool) para:
    *   Convertir el codigo en una imagen PNG usando el renderizador de PlantUML.
    *   Subir el diagrama a una estructura organizada en Google Drive usando la API oficial de Google.

---

## Requisitos e Instalacion

### 1. Clonar el repositorio e instalar dependencias
Este proyecto utiliza uv para una gestion ultra-rapida de paquetes.

`ash
# Instalar dependencias
crewai install
`

### 2. Configuracion del Entorno (.env)
Crea un archivo .env en la raiz del proyecto con las siguientes variables:

`env
MODEL=gpt-4o-mini  # O tu modelo preferido
OPENAI_API_KEY=tu_api_key_aqui
`

---

## Integracion con Google Drive (Paso a Paso)

Para que el sistema pueda subir los diagramas a tu Drive, necesitas un archivo de credenciales:

1.  Ve a Google Cloud Console (https://console.cloud.google.com/).
2.  Crea un nuevo proyecto.
3.  Habilita la Google Drive API.
4.  Configura la Pantalla de Consentimiento OAuth (selecciona 'External' y a�ade tu email como usuario de prueba).
5.  Ve a Credenciales -> Crear Credenciales -> ID de cliente de OAuth.
6.  Selecciona Aplicacion de escritorio.
7.  Descarga el archivo JSON.
8.  IMPORTANTE: Renombra el archivo descargado a client_secret_XXXX.json (asegurate de que el nombre coincida con el que busca la herramienta en custom_tool.py) y colocalo en la raiz del proyecto.

---

## Como usar el proyecto

1.  Escribe la descripcion de tu sistema en el archivo system.txt.
2.  Ejecuta el flujo principal:
    `ash
    crewai flow kickoff
    `
3.  La primera vez que lo ejecutes, se abrira una ventana en tu navegador pidiendo permiso para acceder a Google Drive. Autoriza la aplicacion.
4.  Busca tus diagramas en tu Google Drive dentro de la carpeta: Diagramas UML / [Nombre de tu Proyecto].

---

## Estructura del Proyecto

*   src/diagramas_uml/main.py: Orquestador principal del flujo.
*   crews/crew_analisis/: Logica de analisis de arquitectura.
*   crews/crew_desarrollo/: Logica de generacion y subida de diagramas.
*   src/diagramas_uml/crews/crew_desarrollo/src/crew_desarrollo/tools/custom_tool.py: Herramienta de integracion con Google Drive.
*   output/: Logs locales y reportes generados.

---

