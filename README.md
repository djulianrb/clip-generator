# AI Video Clip Generator

Este proyecto permite descargar videos de YouTube y generar automáticamente clips verticales (9:16) optimizados para TikTok, Reels y Shorts.

## Características principales

- **Audio en Español automático**: Busca y descarga la pista de doblaje en español si está disponible.
- **Formato Vertical Inteligente**: Ajusta el video al centro y rellena el fondo con una versión desenfocada del mismo video.
- **Superposición de Texto**: Agrega el título del video (con soporte multi-línea) y el número de parte ("Parte X") centrados.
- **Procesamiento por lotes**: Divide videos largos en segmentos de 60 segundos automáticamente.

## Instalación

Si es la primera vez que usas el proyecto, ejecuta el script de configuración:

```bash
bash setup.sh
```

Esto instalará `ffmpeg`, creará el entorno virtual e instalará las dependencias necesarias.

## Uso

Para generar clips de cualquier video de YouTube, usa el siguiente comando desde la terminal:

```bash
./venv/bin/python clip_youtube.py "URL_DEL_VIDEO"
```

### Ejemplo:
```bash
./venv/bin/python clip_youtube.py "https://www.youtube.com/watch?v=zRtGL0-5rg4"
```

Los clips resultantes se guardarán en la carpeta `output_clips/`.

## Notas sobre el Audio en Español

El script está configurado para buscar automáticamente la pista de doblaje en español. Si un video tiene varios idiomas, priorizará siempre el español. 

### Solución de problemas:
Si un video se descarga en **inglés** por error:
1.  Borra el archivo temporal que se descargó: `rm downloaded_video.mp4`
2.  Asegúrate de tener conexión a internet y vuelve a correr el comando. El script intentará una detección más profunda.

## Estructura del Proyecto

- `clip_youtube.py`: Script principal para descargar y procesar videos de YouTube.
- `clipper.py`: Lógica de edición de video y superposición de texto.
- `venv/`: Entorno virtual de Python (donde viven las librerías).
- `output_clips/`: Carpeta donde se guardan los resultados.
