"""
Configuración general del juego "¿Quién quiere ser programador?".

Aquí se concentran las constantes (tamaños, colores, rutas, reglas del
juego) para que los demás módulos no tengan valores "mágicos" repetidos.
Si se quiere cambiar una regla (por ejemplo, el tiempo por pregunta),
solo se modifica en este archivo.
"""
import os

#region Rutas de archivos
# Las rutas se calculan desde la ubicación de este archivo para que el
# juego funcione aunque se ejecute desde otra carpeta (igual que en la
# Práctica 5).
CARPETA_CODIGO = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_CODIGO)
CARPETA_RECURSOS = os.path.join(CARPETA_PROYECTO, "recursos")
CARPETA_IMAGENES = os.path.join(CARPETA_RECURSOS, "imagenes")
CARPETA_SONIDOS = os.path.join(CARPETA_RECURSOS, "sonidos")
RUTA_PREGUNTAS = os.path.join(CARPETA_RECURSOS, "preguntas.json")
RUTA_HISTORIAL = os.path.join(CARPETA_RECURSOS, "historial.csv")
#endregion

#region Pantalla
ANCHO = 1000
ALTO = 650
FPS = 60
TITULO = "¿Quién quiere ser programador?"
#endregion

#region Colores (inspirados en los colores de Python: azul y amarillo)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
GRIS = (140, 145, 160)
GRIS_OSCURO = (55, 60, 75)
AZUL_PYTHON = (55, 118, 171)
AZUL_OSCURO = (18, 30, 62)
AZUL_PANEL = (24, 40, 82)
AMARILLO_PYTHON = (255, 212, 59)
VERDE = (46, 160, 90)
ROJO = (200, 60, 60)
CIAN = (110, 200, 255)
FONDO_CODIGO = (12, 16, 28)
#endregion

#region Reglas del juego
TIEMPO_POR_PREGUNTA = 45     # segundos para responder cada pregunta
PREGUNTAS_POR_RANGO = 3      # 4 rangos x 3 preguntas = 12 niveles
LETRAS = "ABCD"              # letras de las 4 opciones

# XP (puntos de experiencia) que vale cada uno de los 12 niveles.
ESCALERA_XP = [100, 200, 300, 500, 800, 1200, 2000, 3000, 5000, 8000, 12000, 20000]

# Niveles que funcionan como "checkpoint": al superarlos, esos XP quedan
# asegurados aunque después se falle una pregunta.
CHECKPOINTS = (3, 6, 9)

# Rangos del jugador. Cada rango agrupa 3 niveles y tiene su imagen.
RANGOS = [
    {"nombre": "Aprendiz", "imagen": "aprendiz.png"},
    {"nombre": "Junior", "imagen": "junior.png"},
    {"nombre": "Desarrollador", "imagen": "desarrollador.png"},
    {"nombre": "Senior", "imagen": "senior.png"},
]
SIN_RANGO = "Sin certificación"
#endregion

#region Estados (pantallas) del juego
ESTADO_INICIO = "inicio"
ESTADO_PREGUNTA = "pregunta"
ESTADO_RESPUESTA = "respuesta"
ESTADO_FIN = "fin"
#endregion

#region Voz
IDIOMA_RECONOCIMIENTO = "es-CR"   # mismo idioma que usa el asistente del curso
SEGUNDOS_GRABACION = 3            # tiempo que se escucha el micrófono
VELOCIDAD_VOZ = 175               # palabras por minuto aproximadas
#endregion
