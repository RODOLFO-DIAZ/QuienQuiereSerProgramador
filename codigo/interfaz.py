"""
Módulo de interfaz.

La clase Interfaz se encarga solo de DIBUJAR: fondo, textos, botones,
escalera de niveles, comodines y temporizador. No decide reglas del
juego; recibe la información (partida, tiempo, mensajes) y la muestra.

Se reutiliza la idea de la función mostrar_texto() del juego del
restaurante visto en clase.
"""
import os

import pygame

from configuracion import (
    ALTO, AMARILLO_PYTHON, ANCHO, AZUL_OSCURO, AZUL_PANEL, AZUL_PYTHON, BLANCO,
    CARPETA_IMAGENES, CHECKPOINTS, CIAN, ESCALERA_XP, FONDO_CODIGO, GRIS,
    GRIS_OSCURO, LETRAS, RANGOS, ROJO, SIN_RANGO, TIEMPO_POR_PREGUNTA, VERDE,
)

#region Posiciones fijas de la pantalla
PANEL_PREGUNTA = pygame.Rect(20, 66, 700, 350)
BARRA_INFERIOR = pygame.Rect(20, 592, 700, 46)
PANEL_DERECHO = pygame.Rect(740, 66, 240, 572)
RECT_TEMPORIZADOR = pygame.Rect(740, 592, 240, 46)

# Rectángulos de las 4 opciones (2 columnas x 2 filas).
RECTS_OPCIONES = [
    pygame.Rect(20, 430, 340, 70),
    pygame.Rect(380, 430, 340, 70),
    pygame.Rect(20, 510, 340, 70),
    pygame.Rect(380, 510, 340, 70),
]

# Rectángulos de los 3 comodines, en el orden de las teclas 1, 2 y 3.
NOMBRES_COMODINES = ["depurar", "documentacion", "refactorizar"]
RECTS_COMODINES = [pygame.Rect(745 + i * 80, 528, 70, 56) for i in range(3)]
#endregion


#region Funciones de apoyo
def cargar_imagen(nombre, tamano=None):
    """
    Carga una imagen de recursos/imagenes y opcionalmente la escala.

    Si la imagen no existe, devuelve None y el juego sigue funcionando
    (mismo manejo de errores que en los juegos del curso).

    Parámetros:
        nombre (str): nombre del archivo, por ejemplo "trofeo.png".
        tamano (tuple): (ancho, alto) deseado, o None para dejarla igual.

    Retorna:
        pygame.Surface o None: la imagen cargada.
    """
    ruta = os.path.join(CARPETA_IMAGENES, nombre)
    try:
        imagen = pygame.image.load(ruta).convert_alpha()
    except (pygame.error, FileNotFoundError):
        print(f"Advertencia: no se pudo cargar la imagen '{nombre}'.")
        return None
    if tamano:
        imagen = pygame.transform.smoothscale(imagen, tamano)
    return imagen


def envolver_texto(texto, fuente, ancho_maximo):
    """
    Divide un texto largo en varias líneas que quepan en un ancho dado.

    Parámetros:
        texto (str): texto a dividir.
        fuente (pygame.font.Font): fuente con la que se va a dibujar.
        ancho_maximo (int): ancho máximo en píxeles de cada línea.

    Retorna:
        list: lista de líneas (str).
    """
    lineas = []
    for parrafo in texto.split("\n"):
        linea_actual = ""
        for palabra in parrafo.split(" "):
            prueba = f"{linea_actual} {palabra}".strip()
            if fuente.size(prueba)[0] <= ancho_maximo:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        lineas.append(linea_actual)
    return lineas
#endregion


class Interfaz:
    """Dibuja todas las pantallas del juego."""

    #region Inicialización
    def __init__(self, pantalla):
        """
        Prepara fuentes e imágenes.

        Parámetros:
            pantalla (pygame.Surface): ventana donde se dibuja.
        """
        self.pantalla = pantalla

        # Fuentes del sistema (Windows trae Segoe UI y Consolas).
        self.fuente_titulo = pygame.font.SysFont("segoeui", 46, bold=True)
        self.fuente_subtitulo = pygame.font.SysFont("segoeui", 28, bold=True)
        self.fuente_pregunta = pygame.font.SysFont("segoeui", 24, bold=True)
        self.fuente_texto = pygame.font.SysFont("segoeui", 20)
        self.fuente_negrita = pygame.font.SysFont("segoeui", 20, bold=True)
        self.fuente_chica = pygame.font.SysFont("segoeui", 16)
        self.fuente_opcion = pygame.font.SysFont("segoeui", 21, bold=True)
        self.fuente_opcion_chica = pygame.font.SysFont("segoeui", 17, bold=True)
        self.fuente_codigo = pygame.font.SysFont("consolas", 19)

        # Imágenes
        self.fondo = cargar_imagen("fondo.png", (ANCHO, ALTO))
        self.logo_chico = cargar_imagen("logo.png", (40, 40))
        self.logo_grande = cargar_imagen("logo.png", (110, 110))
        self.trofeo = cargar_imagen("trofeo.png", (130, 130))
        self.trofeo_chico = cargar_imagen("trofeo.png", (20, 20))
        self.icono_correcto = cargar_imagen("correcto.png", (56, 56))
        self.icono_incorrecto = cargar_imagen("incorrecto.png", (56, 56))
        self.icono_incorrecto_grande = cargar_imagen("incorrecto.png", (120, 120))
        self.icono_reloj = cargar_imagen("reloj.png", (28, 28))
        self.icono_microfono = cargar_imagen("microfono.png", (26, 26))
        self.icono_pista = cargar_imagen("documentacion.png", (26, 26))
        self.iconos_comodines = {
            nombre: cargar_imagen(f"{nombre}.png", (34, 34)) for nombre in NOMBRES_COMODINES
        }
        self.imagenes_rango = {
            rango["nombre"]: cargar_imagen(rango["imagen"], (64, 64)) for rango in RANGOS
        }
        self.imagenes_rango_grandes = {
            rango["nombre"]: cargar_imagen(rango["imagen"], (120, 120)) for rango in RANGOS
        }
    #endregion

    #region Herramientas de dibujo
    def mostrar_texto(self, texto, fuente, color, x, y, alineacion="centro"):
        """
        Dibuja un texto en la pantalla.

        Parámetros:
            texto (str): texto a mostrar.
            fuente (pygame.font.Font): fuente a usar.
            color (tuple): color RGB.
            x, y (int): posición de referencia.
            alineacion (str): "centro" (x, y es el centro) o "izquierda"
                (x, y es la esquina superior izquierda).

        Retorna:
            pygame.Rect: el rectángulo que ocupa el texto.
        """
        superficie = fuente.render(texto, True, color)
        rect = superficie.get_rect()
        if alineacion == "centro":
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.pantalla.blit(superficie, rect)
        return rect

    def panel(self, rect, color=AZUL_PANEL, transparencia=215, borde=None, radio=14):
        """
        Dibuja un rectángulo redondeado y semitransparente.

        Parámetros:
            rect (pygame.Rect): posición y tamaño.
            color (tuple): color de relleno.
            transparencia (int): 0 (invisible) a 255 (sólido).
            borde (tuple): color del borde, o None para no dibujarlo.
            radio (int): redondeo de las esquinas.
        """
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(capa, (*color, transparencia), capa.get_rect(), border_radius=radio)
        self.pantalla.blit(capa, rect.topleft)
        if borde:
            pygame.draw.rect(self.pantalla, borde, rect, 2, border_radius=radio)

    def dibujar_imagen(self, imagen, centro):
        """Dibuja una imagen centrada en un punto, si la imagen existe."""
        if imagen:
            self.pantalla.blit(imagen, imagen.get_rect(center=centro))

    def dibujar_fondo(self):
        """Dibuja la imagen de fondo, o un color sólido si no existe."""
        if self.fondo:
            self.pantalla.blit(self.fondo, (0, 0))
        else:
            self.pantalla.fill(AZUL_OSCURO)

    def dibujar_top(self, rect, top):
        """
        Dibuja la tabla con las mejores partidas.

        Parámetros:
            rect (pygame.Rect): zona donde se dibuja la tabla.
            top (list): partidas devueltas por Marcador.top().
        """
        self.panel(rect, borde=AZUL_PYTHON)
        self.dibujar_imagen(self.trofeo_chico, (rect.x + 30, rect.y + 28))
        self.mostrar_texto("Top 5", self.fuente_subtitulo, AMARILLO_PYTHON, rect.x + 48, rect.y + 8, "izquierda")
        if not top:
            self.mostrar_texto("Todavía no hay partidas.", self.fuente_texto, GRIS, rect.centerx, rect.y + 90)
            return
        y = rect.y + 62
        for posicion, partida in enumerate(top, start=1):
            color = AMARILLO_PYTHON if posicion == 1 else BLANCO
            nombre = partida["nombre"][:14]
            self.mostrar_texto(f"{posicion}. {nombre}", self.fuente_negrita, color, rect.x + 20, y, "izquierda")
            self.mostrar_texto(f"{partida['xp']:,} XP", self.fuente_negrita, color, rect.right - 20 - self.fuente_negrita.size(f"{partida['xp']:,} XP")[0], y, "izquierda")
            self.mostrar_texto(partida["rango"], self.fuente_chica, GRIS, rect.x + 42, y + 25, "izquierda")
            y += 52
    #endregion

    #region Pantalla de inicio
    def dibujar_inicio(self, nombre, top, voz_ok, mic_ok, cursor_visible):
        """
        Dibuja la pantalla de bienvenida donde se escribe el nombre.

        Parámetros:
            nombre (str): nombre escrito hasta ahora.
            top (list): mejores partidas para mostrar.
            voz_ok (bool): si la voz está disponible.
            mic_ok (bool): si el micrófono está disponible.
            cursor_visible (bool): para hacer parpadear el cursor.
        """
        self.dibujar_fondo()
        self.dibujar_imagen(self.logo_grande, (ANCHO // 2, 85))
        self.mostrar_texto("¿Quién quiere ser", self.fuente_subtitulo, BLANCO, ANCHO // 2, 170)
        self.mostrar_texto("PROGRAMADOR?", self.fuente_titulo, AMARILLO_PYTHON, ANCHO // 2, 215)

        # Caja de nombre e instrucciones
        caja = pygame.Rect(50, 270, 520, 330)
        self.panel(caja, borde=AZUL_PYTHON)
        self.mostrar_texto("Escribe tu nombre:", self.fuente_negrita, BLANCO, caja.x + 25, caja.y + 18, "izquierda")
        campo = pygame.Rect(caja.x + 25, caja.y + 52, caja.width - 50, 46)
        pygame.draw.rect(self.pantalla, FONDO_CODIGO, campo, border_radius=8)
        pygame.draw.rect(self.pantalla, AMARILLO_PYTHON, campo, 2, border_radius=8)
        texto_nombre = nombre + ("|" if cursor_visible else "")
        self.mostrar_texto(texto_nombre, self.fuente_subtitulo, BLANCO, campo.x + 12, campo.y + 4, "izquierda")
        self.mostrar_texto("Presiona ENTER para comenzar", self.fuente_negrita, CIAN, caja.centerx, caja.y + 125)

        reglas = [
            "• 12 preguntas de Python: de Aprendiz a Senior.",
            "• Checkpoints en los niveles 3, 6 y 9.",
            "• Responde con A, B, C, D, con clic o con la V (voz).",
            "• Comodines: 1 Depurar · 2 Documentación · 3 Refactorizar.",
            f"• Tienes {TIEMPO_POR_PREGUNTA} segundos por pregunta.",
        ]
        y = caja.y + 160
        for regla in reglas:
            self.mostrar_texto(regla, self.fuente_texto, BLANCO, caja.x + 25, y, "izquierda")
            y += 30

        # Tabla de mejores puntajes
        self.dibujar_top(pygame.Rect(600, 270, 350, 330), top)

        # Estado de la voz y el micrófono
        estado_voz = "Voz: activa" if voz_ok else "Voz: no disponible"
        estado_mic = "Micrófono: listo" if mic_ok else "Micrófono: no disponible (usa el teclado)"
        self.mostrar_texto(f"{estado_voz}   ·   {estado_mic}   ·   ESC: salir", self.fuente_chica, GRIS, ANCHO // 2, 625)
    #endregion

    #region Pantalla de juego
    def dibujar_juego(self, partida, tiempo_restante, pausado, mensaje, revelado=None, mouse=(0, 0)):
        """
        Dibuja la pantalla de pregunta (y la retroalimentación si ya se respondió).

        Parámetros:
            partida (Partida): partida en curso.
            tiempo_restante (float): segundos que quedan.
            pausado (bool): True si el tiempo está detenido (leyendo o escuchando).
            mensaje (str): aviso temporal para la barra inferior.
            revelado (dict): None mientras se responde; después contiene
                "elegida" (int o None), "acerto" (bool) y "tiempo_agotado" (bool).
            mouse (tuple): posición del ratón, para resaltar la opción.
        """
        self.dibujar_fondo()
        self._dibujar_encabezado(partida)
        # Después de responder, la explicación ocupa el lugar de la pregunta.
        if revelado:
            self._dibujar_retroalimentacion(partida.pregunta_actual, revelado)
        else:
            self._dibujar_pregunta(partida.pregunta_actual)
        self._dibujar_opciones(partida, revelado, mouse)
        self._dibujar_escalera(partida)
        self._dibujar_comodines(partida)
        self._dibujar_temporizador(tiempo_restante, pausado)
        self._dibujar_barra_inferior(partida, mensaje, revelado)

    def _dibujar_encabezado(self, partida):
        """Dibuja el título, el nombre del jugador y sus XP."""
        self.dibujar_imagen(self.logo_chico, (42, 33))
        self.mostrar_texto("¿Quién quiere ser programador?", self.fuente_negrita, AMARILLO_PYTHON, 70, 18, "izquierda")
        texto = f"{partida.nombre}   ·   {partida.xp_acumulado():,} XP"
        ancho = self.fuente_negrita.size(texto)[0]
        self.mostrar_texto(texto, self.fuente_negrita, BLANCO, 980 - ancho, 18, "izquierda")

    def _dibujar_pregunta(self, pregunta):
        """Dibuja el enunciado y, si tiene, el bloque de código."""
        self.panel(PANEL_PREGUNTA, borde=AZUL_PYTHON)
        y = PANEL_PREGUNTA.y + 18
        for linea in envolver_texto(pregunta.texto, self.fuente_pregunta, PANEL_PREGUNTA.width - 40):
            self.mostrar_texto(linea, self.fuente_pregunta, BLANCO, PANEL_PREGUNTA.x + 20, y, "izquierda")
            y += 32

        if pregunta.codigo:
            lineas_codigo = pregunta.codigo.split("\n")
            alto = len(lineas_codigo) * 24 + 20
            caja = pygame.Rect(PANEL_PREGUNTA.x + 20, y + 10, PANEL_PREGUNTA.width - 40, alto)
            pygame.draw.rect(self.pantalla, FONDO_CODIGO, caja, border_radius=8)
            pygame.draw.rect(self.pantalla, GRIS_OSCURO, caja, 1, border_radius=8)
            y_codigo = caja.y + 10
            for linea in lineas_codigo:
                self.mostrar_texto(linea, self.fuente_codigo, (205, 230, 255), caja.x + 16, y_codigo, "izquierda")
                y_codigo += 24

    def _dibujar_opciones(self, partida, revelado, mouse):
        """Dibuja los 4 botones de respuesta con el color según su estado."""
        pregunta = partida.pregunta_actual
        for indice, rect in enumerate(RECTS_OPCIONES):
            eliminada = indice in partida.eliminadas
            color_fondo, color_borde, color_texto = AZUL_PANEL, CIAN, BLANCO

            if revelado:
                if indice == pregunta.correcta:
                    color_fondo, color_borde = VERDE, BLANCO
                elif indice == revelado["elegida"]:
                    color_fondo, color_borde = ROJO, BLANCO
            elif eliminada:
                color_fondo, color_borde, color_texto = GRIS_OSCURO, GRIS_OSCURO, GRIS
            elif rect.collidepoint(mouse):
                color_borde = AMARILLO_PYTHON

            self.panel(rect, color_fondo, 235, color_borde, radio=35)

            # Círculo con la letra
            centro_letra = (rect.x + 35, rect.centery)
            pygame.draw.circle(self.pantalla, GRIS if eliminada and not revelado else AMARILLO_PYTHON, centro_letra, 20)
            self.mostrar_texto(LETRAS[indice], self.fuente_opcion, AZUL_OSCURO, *centro_letra)

            if eliminada and not revelado:
                continue  # el comodín Depurar ocultó esta opción
            self._dibujar_texto_opcion(pregunta.opciones[indice], rect, color_texto)

    def _dibujar_texto_opcion(self, texto, rect, color):
        """Dibuja el texto de una opción achicándolo si no cabe."""
        ancho_disponible = rect.width - 85
        fuente = self.fuente_opcion
        if fuente.size(texto)[0] > ancho_disponible:
            fuente = self.fuente_opcion_chica
        lineas = envolver_texto(texto, fuente, ancho_disponible)[:2]
        alto_linea = fuente.get_linesize()
        y = rect.centery - alto_linea * len(lineas) // 2
        for linea in lineas:
            self.mostrar_texto(linea, fuente, color, rect.x + 68, y, "izquierda")
            y += alto_linea

    def _dibujar_escalera(self, partida):
        """Dibuja el rango actual y la escalera de los 12 niveles con sus XP."""
        self.panel(PANEL_DERECHO, borde=AZUL_PYTHON)
        rango = partida.rango_actual()["nombre"]
        self.dibujar_imagen(self.imagenes_rango.get(rango), (PANEL_DERECHO.x + 50, PANEL_DERECHO.y + 45))
        self.mostrar_texto("Rango actual", self.fuente_chica, GRIS, PANEL_DERECHO.x + 95, PANEL_DERECHO.y + 22, "izquierda")
        self.mostrar_texto(rango, self.fuente_subtitulo, AMARILLO_PYTHON, PANEL_DERECHO.x + 95, PANEL_DERECHO.y + 40, "izquierda")

        # Nivel 12 arriba, nivel 1 abajo.
        for nivel in range(partida.total_niveles, 0, -1):
            y = 160 + (partida.total_niveles - nivel) * 30
            fila = pygame.Rect(PANEL_DERECHO.x + 8, y, PANEL_DERECHO.width - 16, 27)
            if nivel == partida.nivel and not partida.gano:
                pygame.draw.rect(self.pantalla, AMARILLO_PYTHON, fila, border_radius=6)
                color = AZUL_OSCURO
            elif nivel <= partida.niveles_superados:
                color = VERDE
            elif nivel in CHECKPOINTS or nivel == partida.total_niveles:
                color = AMARILLO_PYTHON
            else:
                color = BLANCO
            self.mostrar_texto(f"{nivel:>2}", self.fuente_negrita, color, fila.x + 10, fila.y + 1, "izquierda")
            xp = f"{ESCALERA_XP[nivel - 1]:,} XP"
            self.mostrar_texto(xp, self.fuente_negrita, color, fila.x + 50, fila.y + 1, "izquierda")
            if nivel in CHECKPOINTS:
                # Rombo amarillo que marca los checkpoints.
                cx, cy = fila.right - 16, fila.centery
                puntos = [(cx, cy - 8), (cx + 8, cy), (cx, cy + 8), (cx - 8, cy)]
                pygame.draw.polygon(self.pantalla, color if color == AZUL_OSCURO else AMARILLO_PYTHON, puntos)
            elif nivel == partida.total_niveles:
                self.dibujar_imagen(self.trofeo_chico, (fila.right - 16, fila.centery))

    def _dibujar_comodines(self, partida):
        """Dibuja los 3 comodines; los ya usados se ven apagados."""
        for numero, (nombre, rect) in enumerate(zip(NOMBRES_COMODINES, RECTS_COMODINES), start=1):
            disponible = partida.comodines[nombre]
            self.panel(rect, AZUL_PYTHON if disponible else GRIS_OSCURO, 230, BLANCO if disponible else GRIS, radio=10)
            icono = self.iconos_comodines[nombre]
            if icono:
                icono = icono.copy()
                if not disponible:
                    icono.set_alpha(70)
                self.pantalla.blit(icono, icono.get_rect(center=(rect.centerx, rect.y + 22)))
            self.mostrar_texto(str(numero), self.fuente_chica, BLANCO if disponible else GRIS, rect.centerx, rect.bottom - 9)

    def _dibujar_temporizador(self, tiempo_restante, pausado):
        """Dibuja la barra del tiempo; cambia de color cuando queda poco."""
        self.panel(RECT_TEMPORIZADOR, borde=AZUL_PYTHON, radio=10)
        self.dibujar_imagen(self.icono_reloj, (RECT_TEMPORIZADOR.x + 22, RECT_TEMPORIZADOR.centery))
        barra = pygame.Rect(RECT_TEMPORIZADOR.x + 42, RECT_TEMPORIZADOR.y + 14, 140, 18)
        pygame.draw.rect(self.pantalla, GRIS_OSCURO, barra, border_radius=9)
        proporcion = max(0, tiempo_restante) / TIEMPO_POR_PREGUNTA
        if proporcion > 0.5:
            color = VERDE
        elif proporcion > 0.2:
            color = AMARILLO_PYTHON
        else:
            color = ROJO
        relleno = pygame.Rect(barra.x, barra.y, int(barra.width * proporcion), barra.height)
        pygame.draw.rect(self.pantalla, color, relleno, border_radius=9)
        texto = "II" if pausado else f"{int(tiempo_restante + 0.99)}s"
        self.mostrar_texto(texto, self.fuente_negrita, BLANCO, RECT_TEMPORIZADOR.right - 28, RECT_TEMPORIZADOR.centery)

    def _dibujar_barra_inferior(self, partida, mensaje, revelado):
        """Muestra un aviso, la pista del comodín o la ayuda de teclas."""
        self.panel(BARRA_INFERIOR, radio=10)
        x = BARRA_INFERIOR.x + 14
        y = BARRA_INFERIOR.y + 11
        if mensaje:
            self.dibujar_imagen(self.icono_microfono, (x + 12, BARRA_INFERIOR.centery))
            self.mostrar_texto(mensaje, self.fuente_negrita, CIAN, x + 34, y, "izquierda")
        elif partida.pista_visible and not revelado:
            self.dibujar_imagen(self.icono_pista, (x + 12, BARRA_INFERIOR.centery))
            pista = envolver_texto("Pista: " + partida.pregunta_actual.pista, self.fuente_negrita, BARRA_INFERIOR.width - 60)[0]
            self.mostrar_texto(pista, self.fuente_negrita, AMARILLO_PYTHON, x + 34, y, "izquierda")
        else:
            ayuda = "A-D responder · 1-3 comodines · V voz · R repetir · M silencio · ESC salir"
            self.mostrar_texto(ayuda, self.fuente_chica, GRIS, BARRA_INFERIOR.centerx, BARRA_INFERIOR.centery)

    def _dibujar_retroalimentacion(self, pregunta, revelado):
        """Dibuja sobre la pregunta si se acertó o no, con la explicación."""
        self.panel(PANEL_PREGUNTA, AZUL_OSCURO, 240, AMARILLO_PYTHON)
        x = PANEL_PREGUNTA.x + 30
        if revelado["acerto"]:
            icono, titulo, color = self.icono_correcto, "¡Correcto!", VERDE
        elif revelado["tiempo_agotado"]:
            icono, titulo, color = self.icono_incorrecto, "¡Se acabó el tiempo!", ROJO
        else:
            icono, titulo, color = self.icono_incorrecto, "Incorrecto", ROJO
        self.dibujar_imagen(icono, (x + 28, PANEL_PREGUNTA.y + 50))
        self.mostrar_texto(titulo, self.fuente_titulo, color, x + 75, PANEL_PREGUNTA.y + 20, "izquierda")

        y = PANEL_PREGUNTA.y + 100
        if not revelado["acerto"]:
            self.mostrar_texto(f"Respuesta correcta: {pregunta.respuesta_correcta()}", self.fuente_pregunta, AMARILLO_PYTHON, x, y, "izquierda")
            y += 40
        for linea in envolver_texto(pregunta.explicacion, self.fuente_texto, PANEL_PREGUNTA.width - 60):
            self.mostrar_texto(linea, self.fuente_texto, BLANCO, x, y, "izquierda")
            y += 28
        self.mostrar_texto("Presiona ESPACIO para continuar", self.fuente_negrita, CIAN, PANEL_PREGUNTA.centerx, PANEL_PREGUNTA.bottom - 28)
    #endregion

    #region Pantalla final
    def dibujar_fin(self, partida, top):
        """
        Dibuja la pantalla de fin de juego con el resultado y el Top 5.

        Parámetros:
            partida (Partida): partida terminada.
            top (list): mejores partidas (ya incluye la recién guardada).
        """
        self.dibujar_fondo()
        rango = partida.rango_final()
        caja = pygame.Rect(50, 40, 520, 560)
        self.panel(caja, borde=AMARILLO_PYTHON)

        if partida.gano:
            imagen = self.trofeo
            titulo = "¡Felicidades!"
            subtitulo = f"{partida.nombre}, ya eres programador Senior"
        else:
            imagen = self.imagenes_rango_grandes.get(rango) or self.icono_incorrecto_grande
            titulo = "Fin del juego"
            subtitulo = f"Buen intento, {partida.nombre}"
        self.dibujar_imagen(imagen, (caja.centerx, caja.y + 95))
        self.mostrar_texto(titulo, self.fuente_titulo, AMARILLO_PYTHON, caja.centerx, caja.y + 200)
        self.mostrar_texto(subtitulo, self.fuente_subtitulo, BLANCO, caja.centerx, caja.y + 250)

        datos = [
            ("XP finales", f"{partida.xp_final():,} XP"),
            ("Rango certificado", rango if rango != SIN_RANGO else "Sin certificación"),
            ("Nivel alcanzado", f"{partida.nivel if not partida.gano else partida.total_niveles} de {partida.total_niveles}"),
            ("Respuestas correctas", str(partida.niveles_superados)),
        ]
        y = caja.y + 300
        for etiqueta, valor in datos:
            self.mostrar_texto(etiqueta, self.fuente_texto, GRIS, caja.x + 60, y, "izquierda")
            ancho = self.fuente_negrita.size(valor)[0]
            self.mostrar_texto(valor, self.fuente_negrita, BLANCO, caja.right - 60 - ancho, y, "izquierda")
            y += 40

        self.mostrar_texto("ESPACIO: jugar otra vez   ·   ESC: salir", self.fuente_negrita, CIAN, caja.centerx, caja.bottom - 35)
        self.dibujar_top(pygame.Rect(600, 40, 350, 330), top)
    #endregion
