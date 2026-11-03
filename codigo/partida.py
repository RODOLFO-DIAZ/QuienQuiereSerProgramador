"""
Módulo de la partida.

La clase Partida contiene las reglas del juego: en qué nivel va el
jugador, cuántos XP tiene, qué comodines le quedan y cuándo termina.
No dibuja nada en pantalla (eso lo hace interfaz.py), así cada módulo
tiene una sola responsabilidad y la lógica se puede probar sin Pygame.
"""
import random

from configuracion import CHECKPOINTS, ESCALERA_XP, RANGOS, SIN_RANGO


class Partida:
    """Estado y reglas de una partida de un jugador."""

    #region Creación de la partida
    def __init__(self, nombre, banco):
        """
        Inicia una partida nueva.

        Parámetros:
            nombre (str): nombre del jugador.
            banco (BancoPreguntas): banco del que se toman las preguntas.
        """
        self.nombre = nombre
        self.banco = banco
        self.preguntas = banco.armar_escalera()
        self.aciertos = 0           # niveles superados
        self.terminada = False
        self.gano = False
        # Comodines disponibles: True = todavía se puede usar.
        self.comodines = {"depurar": True, "documentacion": True, "refactorizar": True}
        self.eliminadas = []        # opciones quitadas con el comodín Depurar
        self.pista_visible = False  # se activa con el comodín Documentación
    #endregion

    #region Información de la partida
    @property
    def nivel(self):
        """Número del nivel actual en la escalera (1 a 12)."""
        return self.aciertos + 1

    @property
    def pregunta_actual(self):
        """Pregunta que el jugador debe responder ahora."""
        return self.preguntas[self.aciertos]

    @property
    def total_niveles(self):
        """Cantidad de niveles de la escalera."""
        return len(self.preguntas)

    @property
    def niveles_superados(self):
        """Cantidad de preguntas respondidas correctamente."""
        return self.total_niveles if self.gano else self.aciertos

    def xp_en_juego(self):
        """XP que se ganan si se responde bien la pregunta actual."""
        return ESCALERA_XP[self.aciertos]

    def xp_acumulado(self):
        """XP del último nivel superado (0 si todavía no supera ninguno)."""
        if self.aciertos == 0:
            return 0
        return ESCALERA_XP[self.aciertos - 1]

    def ultimo_checkpoint(self):
        """Número del último checkpoint superado (0 si no hay ninguno)."""
        if self.gano:
            return self.total_niveles
        superados = [c for c in CHECKPOINTS if c <= self.aciertos]
        return max(superados) if superados else 0

    def xp_final(self):
        """
        Calcula los XP con los que termina la partida.

        Si el jugador ganó, recibe todos los XP. Si falló, conserva solo
        los XP de su último checkpoint.

        Retorna:
            int: XP finales.
        """
        if self.gano:
            return ESCALERA_XP[-1]
        checkpoint = self.ultimo_checkpoint()
        return ESCALERA_XP[checkpoint - 1] if checkpoint > 0 else 0

    def rango_actual(self):
        """Diccionario del rango del nivel que se está jugando."""
        indice = min(self.aciertos // 3, len(RANGOS) - 1)
        return RANGOS[indice]

    def rango_final(self):
        """
        Nombre del rango que el jugador asegura al terminar.

        Cada checkpoint certifica un rango: nivel 3 = Aprendiz, 6 = Junior,
        9 = Desarrollador y 12 (ganar) = Senior.

        Retorna:
            str: nombre del rango o "Sin certificación".
        """
        checkpoint = self.ultimo_checkpoint()
        if checkpoint == 0:
            return SIN_RANGO
        return RANGOS[checkpoint // 3 - 1]["nombre"]
    #endregion

    #region Responder
    def responder(self, indice):
        """
        Registra la respuesta del jugador.

        Parámetros:
            indice (int): opción elegida (0 a 3).

        Retorna:
            bool: True si acertó, False si falló.
        """
        if self.pregunta_actual.es_correcta(indice):
            if self.nivel == self.total_niveles:
                # Respondió bien la última pregunta: ganó el juego.
                self.gano = True
                self.terminada = True
            return True
        self.terminada = True
        return False

    def tiempo_agotado(self):
        """Termina la partida porque se acabó el tiempo de la pregunta."""
        self.terminada = True

    def siguiente(self):
        """Avanza al siguiente nivel después de una respuesta correcta."""
        self.aciertos += 1
        self.eliminadas = []
        self.pista_visible = False
    #endregion

    #region Comodines
    def usar_depurar(self):
        """
        Comodín Depurar: elimina una respuesta incorrecta al azar.

        Retorna:
            int o None: la opción eliminada, o None si ya se usó.
        """
        if not self.comodines["depurar"]:
            return None
        pregunta = self.pregunta_actual
        incorrectas = [
            i for i in range(len(pregunta.opciones))
            if i != pregunta.correcta and i not in self.eliminadas
        ]
        eliminada = random.choice(incorrectas)
        self.eliminadas.append(eliminada)
        self.comodines["depurar"] = False
        return eliminada

    def usar_documentacion(self):
        """
        Comodín Documentación: muestra la pista de la pregunta.

        Retorna:
            str o None: el texto de la pista, o None si ya se usó.
        """
        if not self.comodines["documentacion"]:
            return None
        self.comodines["documentacion"] = False
        self.pista_visible = True
        return self.pregunta_actual.pista

    def usar_refactorizar(self):
        """
        Comodín Refactorizar: cambia la pregunta por otra del mismo nivel.

        Retorna:
            bool: True si se cambió la pregunta, False si no se pudo.
        """
        if not self.comodines["refactorizar"]:
            return False
        nueva = self.banco.reemplazo(self.pregunta_actual, self.preguntas)
        if nueva is None:
            return False
        self.preguntas[self.aciertos] = nueva
        self.comodines["refactorizar"] = False
        self.eliminadas = []
        self.pista_visible = False
        return True
    #endregion
