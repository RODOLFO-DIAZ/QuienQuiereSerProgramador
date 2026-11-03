"""
Módulo del juego.

La clase Juego coordina todo: el ciclo principal de Pygame, las pantallas
(estados), los eventos de teclado y ratón, los sonidos y la voz. Para
hacer su trabajo usa los demás módulos:

    preguntas.py -> BancoPreguntas (carga las preguntas)
    partida.py   -> Partida (reglas: niveles, XP, comodines)
    marcador.py  -> Marcador (historial y Top 5)
    voz.py       -> Voz y Oido (hablar y escuchar)
    interfaz.py  -> Interfaz (dibujar)
"""
import os
import sys

import pygame
from pygame import mixer

from configuracion import (
    ALTO, ANCHO, CARPETA_IMAGENES, CARPETA_SONIDOS, ESTADO_FIN, ESTADO_INICIO,
    ESTADO_PREGUNTA, ESTADO_RESPUESTA, FPS, LETRAS, RUTA_HISTORIAL,
    RUTA_PREGUNTAS, TIEMPO_POR_PREGUNTA, TITULO,
)
from interfaz import NOMBRES_COMODINES, RECTS_COMODINES, RECTS_OPCIONES, Interfaz
from marcador import Marcador
from partida import Partida
from preguntas import BancoPreguntas
from voz import Oido, Voz, interpretar_respuesta, saludo_segun_hora

# Teclas que eligen cada opción (A-D) y cada comodín (1-3).
TECLAS_OPCIONES = {pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3}
TECLAS_COMODINES = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
DURACION_MENSAJE = 3.5  # segundos que se muestra un aviso en la barra inferior


class Juego:
    """Controla el ciclo principal y las pantallas del juego."""

    #region Inicialización
    def __init__(self):
        """Inicia Pygame, carga los recursos y prepara la pantalla de inicio."""
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        try:
            pygame.display.set_icon(pygame.image.load(os.path.join(CARPETA_IMAGENES, "logo.png")))
        except (pygame.error, FileNotFoundError):
            pass
        self.reloj = pygame.time.Clock()

        # Objetos de los demás módulos
        self.interfaz = Interfaz(self.pantalla)
        self.banco = BancoPreguntas(RUTA_PREGUNTAS)
        self.marcador = Marcador(RUTA_HISTORIAL)
        self.voz = Voz()
        self.oido = Oido()

        # Sonido
        self.silencio = False
        self.sonidos = self._cargar_sonidos()
        self._iniciar_musica()

        # Variables de estado
        self.estado = ESTADO_INICIO
        self.ejecutando = True
        self.nombre = ""
        self.partida = None
        self.tiempo_restante = TIEMPO_POR_PREGUNTA
        self.revelado = None       # resultado de la última respuesta
        self.mensaje = ""          # aviso temporal en la barra inferior
        self.tiempo_mensaje = 0
        self.parpadeo = 0          # para el cursor del nombre
        self.top = self.marcador.top()

        self.voz.hablar("Bienvenido a ¿Quién quiere ser programador? Escribe tu nombre y presiona Enter.")

    def _cargar_sonidos(self):
        """
        Carga los efectos de sonido de recursos/sonidos.

        Retorna:
            dict: nombre -> mixer.Sound (o None si el archivo no se pudo cargar).
        """
        sonidos = {}
        for nombre in ["correcto", "incorrecto", "comodin", "victoria"]:
            try:
                sonidos[nombre] = mixer.Sound(os.path.join(CARPETA_SONIDOS, f"{nombre}.wav"))
                sonidos[nombre].set_volume(0.6)
            except (pygame.error, FileNotFoundError):
                print(f"Advertencia: no se pudo cargar el sonido '{nombre}.wav'.")
                sonidos[nombre] = None
        return sonidos

    def _iniciar_musica(self):
        """Reproduce la música de fondo en bucle, como en los juegos del curso."""
        try:
            mixer.music.load(os.path.join(CARPETA_SONIDOS, "musica_fondo.wav"))
            mixer.music.set_volume(0.25)
            mixer.music.play(-1)  # -1 = repetir sin fin
        except pygame.error:
            print("Advertencia: no se pudo cargar la música de fondo.")

    def reproducir(self, nombre):
        """Reproduce un efecto de sonido si existe y el juego no está en silencio."""
        sonido = self.sonidos.get(nombre)
        if sonido and not self.silencio:
            sonido.play()
    #endregion

    #region Ciclo principal
    def ejecutar(self):
        """Ciclo principal: eventos -> lógica -> dibujo, hasta cerrar la ventana."""
        while self.ejecutando:
            segundos = self.reloj.tick(FPS) / 1000  # tiempo desde el cuadro anterior
            self.manejar_eventos()
            self.actualizar(segundos)
            self.dibujar()
            pygame.display.flip()
        self.salir()

    def salir(self):
        """Cierra la voz y Pygame de forma ordenada."""
        self.voz.detener()
        pygame.quit()
        sys.exit()
    #endregion

    #region Eventos
    def manejar_eventos(self):
        """Revisa los eventos y los envía al método de la pantalla actual."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_m and self.estado != ESTADO_INICIO:
                self.alternar_silencio()
            elif self.estado == ESTADO_INICIO:
                self._eventos_inicio(evento)
            elif self.estado == ESTADO_PREGUNTA:
                self._eventos_pregunta(evento)
            elif self.estado == ESTADO_RESPUESTA:
                self._eventos_respuesta(evento)
            elif self.estado == ESTADO_FIN:
                self._eventos_fin(evento)

    def _eventos_inicio(self, evento):
        """Escribir el nombre del jugador y comenzar con ENTER."""
        if evento.type == pygame.TEXTINPUT:
            # TEXTINPUT acepta tildes y ñ (por ejemplo, "Toño").
            if len(self.nombre) < 16:
                self.nombre += evento.text
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_BACKSPACE:
                self.nombre = self.nombre[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.iniciar_partida()

    def _eventos_pregunta(self, evento):
        """Responder, usar comodines, repetir la lectura o responder por voz."""
        if evento.type == pygame.KEYDOWN:
            if evento.key in TECLAS_OPCIONES:
                self.responder(TECLAS_OPCIONES[evento.key])
            elif evento.key in TECLAS_COMODINES:
                self.usar_comodin(NOMBRES_COMODINES[TECLAS_COMODINES[evento.key]])
            elif evento.key == pygame.K_r:
                self.leer_pregunta()
            elif evento.key == pygame.K_v:
                self.escuchar_respuesta()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for indice, rect in enumerate(RECTS_OPCIONES):
                if rect.collidepoint(evento.pos):
                    self.responder(indice)
            for indice, rect in enumerate(RECTS_COMODINES):
                if rect.collidepoint(evento.pos):
                    self.usar_comodin(NOMBRES_COMODINES[indice])

    def _eventos_respuesta(self, evento):
        """Continuar con ESPACIO, ENTER o clic después de ver la explicación."""
        continuar = (
            (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN))
            or (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1)
        )
        if continuar:
            self.continuar()

    def _eventos_fin(self, evento):
        """Volver a jugar con ESPACIO (ESC ya se revisa en manejar_eventos)."""
        if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.estado = ESTADO_INICIO
            self.voz.hablar("Escribe tu nombre y presiona Enter.")
    #endregion

    #region Lógica del juego
    def iniciar_partida(self):
        """Crea una partida nueva con el nombre escrito."""
        nombre = self.nombre.strip() or "Anónimo"
        self.partida = Partida(nombre, self.banco)
        self.voz.hablar(f"{saludo_segun_hora()}, {nombre}. ¡Comencemos!")
        self.mostrar_pregunta(saludar=False)

    def mostrar_pregunta(self, saludar=True):
        """Prepara la pantalla para la pregunta actual y la lee en voz alta."""
        self.estado = ESTADO_PREGUNTA
        self.tiempo_restante = TIEMPO_POR_PREGUNTA
        self.revelado = None
        self.mensaje = ""
        self.oido.tomar_resultado()  # descarta una respuesta de voz vieja
        self.leer_pregunta(reemplazar=saludar)

    def leer_pregunta(self, reemplazar=True):
        """
        Lee la pregunta actual en voz alta.

        Parámetros:
            reemplazar (bool): si es False, la lectura se agrega después del
                saludo inicial en lugar de cortarlo.
        """
        texto = self.partida.pregunta_actual.texto_para_voz(self.partida.nivel, self.partida.xp_en_juego())
        self.voz.hablar(texto, interrumpir=reemplazar)

    def responder(self, indice):
        """
        Procesa la opción elegida por el jugador.

        Parámetros:
            indice (int): opción elegida (0 a 3).
        """
        if indice in self.partida.eliminadas:
            return  # no se puede elegir una opción eliminada por Depurar
        acerto = self.partida.responder(indice)
        self._mostrar_resultado(indice, acerto, tiempo_agotado=False)

    def _mostrar_resultado(self, elegida, acerto, tiempo_agotado):
        """Pasa a la pantalla de retroalimentación con sonido y voz."""
        self.estado = ESTADO_RESPUESTA
        self.revelado = {"elegida": elegida, "acerto": acerto, "tiempo_agotado": tiempo_agotado}
        self.mensaje = ""
        pregunta = self.partida.pregunta_actual
        if acerto:
            self.reproducir("correcto")
            self.voz.hablar("¡Correcto! " + pregunta.explicacion)
        else:
            self.reproducir("incorrecto")
            inicio = "Se acabó el tiempo." if tiempo_agotado else "Incorrecto."
            self.voz.hablar(f"{inicio} La respuesta correcta era la {pregunta.respuesta_correcta()}. {pregunta.explicacion}")

    def continuar(self):
        """Después de la explicación: sigue a la próxima pregunta o termina."""
        if self.partida.terminada:
            self.terminar_partida()
        else:
            self.partida.siguiente()
            self.mostrar_pregunta()

    def terminar_partida(self):
        """Guarda el resultado en el historial y muestra la pantalla final."""
        partida = self.partida
        nivel = partida.total_niveles if partida.gano else partida.nivel
        self.marcador.guardar(partida.nombre, partida.xp_final(), partida.rango_final(), nivel, partida.niveles_superados)
        self.top = self.marcador.top()
        self.estado = ESTADO_FIN
        if partida.gano:
            self.reproducir("victoria")
            self.voz.hablar(f"¡Felicidades {partida.nombre}! Ya eres programador Senior, con {partida.xp_final()} XP.")
        else:
            self.voz.hablar(f"Fin del juego. Terminas con {partida.xp_final()} XP. Rango: {partida.rango_final()}.")

    def usar_comodin(self, nombre):
        """
        Usa uno de los tres comodines si todavía está disponible.

        Parámetros:
            nombre (str): "depurar", "documentacion" o "refactorizar".
        """
        if nombre == "depurar":
            eliminada = self.partida.usar_depurar()
            if eliminada is not None:
                self.reproducir("comodin")
                self.voz.hablar(f"Depurando: la opción {LETRAS[eliminada]} es incorrecta.")
        elif nombre == "documentacion":
            pista = self.partida.usar_documentacion()
            if pista is not None:
                self.reproducir("comodin")
                self.voz.hablar("Pista: " + pista)
        elif nombre == "refactorizar":
            if self.partida.usar_refactorizar():
                self.reproducir("comodin")
                self.mostrar_pregunta()

    def escuchar_respuesta(self):
        """Activa el micrófono para responder por voz (tecla V)."""
        if not self.oido.disponible:
            self.avisar("Micrófono no disponible. Usa las teclas A, B, C o D.")
        elif self.voz.hablando:
            self.avisar("Espera a que termine de leer y presiona V otra vez.")
        elif not self.oido.escuchando:
            self.oido.escuchar()
            self.avisar("Escuchando... di A, B, C o D", duracion=99)

    def alternar_silencio(self):
        """Tecla M: silencia o reactiva la música, los efectos y la voz."""
        self.silencio = not self.silencio
        self.voz.activa = not self.silencio
        if self.silencio:
            mixer.music.pause()
        else:
            mixer.music.unpause()

    def avisar(self, texto, duracion=DURACION_MENSAJE):
        """Muestra un aviso temporal en la barra inferior."""
        self.mensaje = texto
        self.tiempo_mensaje = duracion

    def actualizar(self, segundos):
        """
        Lógica que corre en cada cuadro: avisos, micrófono y temporizador.

        Parámetros:
            segundos (float): tiempo transcurrido desde el cuadro anterior.
        """
        self.parpadeo = (self.parpadeo + segundos) % 1

        if self.mensaje:
            self.tiempo_mensaje -= segundos
            if self.tiempo_mensaje <= 0:
                self.mensaje = ""

        if self.estado != ESTADO_PREGUNTA:
            return

        # ¿Terminó de escuchar el micrófono?
        texto = self.oido.tomar_resultado()
        if texto is not None:
            opcion = interpretar_respuesta(texto)
            if opcion is None or opcion in self.partida.eliminadas:
                self.avisar(self.oido.error or f"Escuché '{texto}'. Di A, B, C o D.")
            else:
                self.avisar(f"Escuché: {LETRAS[opcion]}")
                self.responder(opcion)
                return

        # El tiempo se detiene mientras se lee la pregunta o se escucha.
        if not self.tiempo_pausado():
            self.tiempo_restante -= segundos
            if self.tiempo_restante <= 0:
                self.partida.tiempo_agotado()
                self._mostrar_resultado(None, False, tiempo_agotado=True)

    def tiempo_pausado(self):
        """True si el temporizador debe estar detenido."""
        return self.voz.hablando or self.oido.escuchando
    #endregion

    #region Dibujo
    def dibujar(self):
        """Dibuja la pantalla que corresponde al estado actual."""
        if self.estado == ESTADO_INICIO:
            self.interfaz.dibujar_inicio(
                self.nombre, self.top, self.voz.disponible, self.oido.disponible, self.parpadeo < 0.5
            )
        elif self.estado in (ESTADO_PREGUNTA, ESTADO_RESPUESTA):
            self.interfaz.dibujar_juego(
                self.partida, self.tiempo_restante, self.tiempo_pausado(),
                self.mensaje, self.revelado, pygame.mouse.get_pos(),
            )
        elif self.estado == ESTADO_FIN:
            self.interfaz.dibujar_fin(self.partida, self.top)
    #endregion
