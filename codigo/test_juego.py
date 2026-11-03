"""
Pruebas automáticas del juego (módulo unittest de Python).

Prueban la lógica que no necesita ventana: preguntas, reglas de la
partida, comodines, marcador y la interpretación de la voz.

Ejecutar desde la carpeta del proyecto:
    python -m unittest discover -s codigo -v
"""
import os
import random
import tempfile
import unittest

from configuracion import CHECKPOINTS, ESCALERA_XP, PREGUNTAS_POR_RANGO, RANGOS, RUTA_PREGUNTAS, SIN_RANGO
from marcador import Marcador
from partida import Partida
from preguntas import BancoPreguntas, Pregunta
from voz import interpretar_respuesta, quitar_tildes, saludo_segun_hora


#region Pruebas del banco de preguntas
class PruebasPreguntas(unittest.TestCase):
    """Revisan que el archivo preguntas.json sea válido."""

    def setUp(self):
        """Carga el banco real antes de cada prueba."""
        self.banco = BancoPreguntas(RUTA_PREGUNTAS)

    def test_cada_pregunta_es_valida(self):
        """Cada pregunta tiene 4 opciones distintas, respuesta válida y explicación."""
        for pregunta in self.banco.preguntas:
            with self.subTest(pregunta=pregunta.texto):
                self.assertEqual(len(pregunta.opciones), 4)
                self.assertEqual(len(set(pregunta.opciones)), 4, "hay opciones repetidas")
                self.assertIn(pregunta.correcta, range(4))
                self.assertIn(pregunta.nivel, range(1, len(RANGOS) + 1))
                self.assertTrue(pregunta.pista)
                self.assertTrue(pregunta.explicacion)

    def test_hay_suficientes_preguntas_por_nivel(self):
        """Cada nivel tiene al menos una pregunta extra para el comodín Refactorizar."""
        for nivel in range(1, len(RANGOS) + 1):
            self.assertGreater(len(self.banco.por_nivel(nivel)), PREGUNTAS_POR_RANGO)

    def test_escalera_ordenada_por_dificultad(self):
        """La escalera tiene 12 preguntas, de la más fácil a la más difícil."""
        escalera = self.banco.armar_escalera()
        self.assertEqual(len(escalera), len(ESCALERA_XP))
        niveles = [p.nivel for p in escalera]
        self.assertEqual(niveles, sorted(niveles))

    def test_mezclar_conserva_la_respuesta_correcta(self):
        """Al mezclar las opciones, la respuesta correcta sigue siendo la misma."""
        original = Pregunta(1, "¿2 + 2?", ["4", "3", "5", "22"], 0)
        for _ in range(20):
            mezclada = original.mezclada()
            self.assertEqual(mezclada.opciones[mezclada.correcta], "4")
        self.assertEqual(original.opciones, ["4", "3", "5", "22"], "no debe cambiar la original")
#endregion


#region Pruebas de la partida
class PruebasPartida(unittest.TestCase):
    """Revisan las reglas: avanzar, perder, checkpoints, ganar y comodines."""

    def setUp(self):
        """Crea una partida nueva con semilla fija para que sea repetible."""
        random.seed(1)
        self.banco = BancoPreguntas(RUTA_PREGUNTAS)
        self.partida = Partida("Prueba", self.banco)

    def responder_bien(self, veces):
        """Responde correctamente varias preguntas seguidas."""
        for _ in range(veces):
            self.assertTrue(self.partida.responder(self.partida.pregunta_actual.correcta))
            if not self.partida.terminada:
                self.partida.siguiente()

    def respuesta_incorrecta(self):
        """Devuelve el índice de una opción incorrecta de la pregunta actual."""
        return (self.partida.pregunta_actual.correcta + 1) % 4

    def test_inicio(self):
        """Una partida nueva empieza en el nivel 1, sin XP."""
        self.assertEqual(self.partida.nivel, 1)
        self.assertEqual(self.partida.xp_acumulado(), 0)
        self.assertFalse(self.partida.terminada)

    def test_fallar_sin_checkpoint_da_cero(self):
        """Si falla antes del primer checkpoint, termina con 0 XP y sin rango."""
        self.responder_bien(2)
        self.assertFalse(self.partida.responder(self.respuesta_incorrecta()))
        self.assertTrue(self.partida.terminada)
        self.assertEqual(self.partida.xp_final(), 0)
        self.assertEqual(self.partida.rango_final(), SIN_RANGO)

    def test_fallar_conserva_el_checkpoint(self):
        """Si falla en el nivel 8, conserva los XP del checkpoint del nivel 6."""
        self.responder_bien(7)
        self.partida.responder(self.respuesta_incorrecta())
        self.assertEqual(self.partida.ultimo_checkpoint(), 6)
        self.assertEqual(self.partida.xp_final(), ESCALERA_XP[CHECKPOINTS[1] - 1])
        self.assertEqual(self.partida.rango_final(), "Junior")

    def test_tiempo_agotado_termina_la_partida(self):
        """Si se acaba el tiempo, la partida termina."""
        self.partida.tiempo_agotado()
        self.assertTrue(self.partida.terminada)
        self.assertFalse(self.partida.gano)

    def test_ganar(self):
        """Al responder bien las 12 preguntas se gana con todos los XP y rango Senior."""
        self.responder_bien(12)
        self.assertTrue(self.partida.gano)
        self.assertEqual(self.partida.xp_final(), ESCALERA_XP[-1])
        self.assertEqual(self.partida.rango_final(), "Senior")
        self.assertEqual(self.partida.niveles_superados, 12)

    def test_depurar_elimina_una_incorrecta_una_sola_vez(self):
        """Depurar quita una opción incorrecta y no se puede volver a usar."""
        eliminada = self.partida.usar_depurar()
        self.assertNotEqual(eliminada, self.partida.pregunta_actual.correcta)
        self.assertIn(eliminada, self.partida.eliminadas)
        self.assertIsNone(self.partida.usar_depurar())

    def test_documentacion_muestra_pista(self):
        """Documentación devuelve la pista y se gasta."""
        pista = self.partida.usar_documentacion()
        self.assertEqual(pista, self.partida.pregunta_actual.pista)
        self.assertTrue(self.partida.pista_visible)
        self.assertIsNone(self.partida.usar_documentacion())

    def test_refactorizar_cambia_la_pregunta(self):
        """Refactorizar cambia la pregunta por otra del mismo nivel."""
        anterior = self.partida.pregunta_actual
        self.assertTrue(self.partida.usar_refactorizar())
        nueva = self.partida.pregunta_actual
        self.assertEqual(nueva.nivel, anterior.nivel)
        self.assertNotEqual(nueva.texto + nueva.codigo, anterior.texto + anterior.codigo)
        self.assertFalse(self.partida.usar_refactorizar())
#endregion


#region Pruebas del marcador
class PruebasMarcador(unittest.TestCase):
    """Revisan que el historial se guarde y que el Top 5 esté ordenado."""

    def setUp(self):
        """Usa un archivo temporal para no tocar el historial real."""
        self.carpeta = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.carpeta.name, "historial.csv")
        self.marcador = Marcador(self.ruta)

    def tearDown(self):
        """Borra la carpeta temporal."""
        self.carpeta.cleanup()

    def test_archivo_nuevo_vacio(self):
        """Un historial nuevo existe y no tiene partidas."""
        self.assertTrue(os.path.exists(self.ruta))
        self.assertEqual(self.marcador.leer_historial(), [])

    def test_guardar_y_top(self):
        """Las partidas se guardan con tildes y el Top se ordena por XP."""
        xp_de_prueba = [300, 20000, 0, 1200, 500, 8000]
        for numero, xp in enumerate(xp_de_prueba):
            self.marcador.guardar(f"Toño {numero}", xp, "Junior", 5, 4)
        self.assertEqual(len(self.marcador.leer_historial()), 6)
        top = self.marcador.top(5)
        self.assertEqual([p["xp"] for p in top], [20000, 8000, 1200, 500, 300])
        self.assertEqual(top[0]["nombre"], "Toño 1")
#endregion


#region Pruebas de la voz
class PruebasVoz(unittest.TestCase):
    """Revisan cómo se interpreta lo que dice el jugador."""

    def test_letras_y_numeros(self):
        """Reconoce letras, su pronunciación y números."""
        casos = {"A": 0, "be": 1, "la ve": 1, "C.": 2, "opción de": 3, "dos": 1, "la cuarta": 3}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_respuesta(texto), esperado)

    def test_usa_la_ultima_palabra(self):
        """En 'voy a la c' la respuesta es C, no la A de 'voy a'."""
        self.assertEqual(interpretar_respuesta("voy a la c"), 2)

    def test_no_entendido(self):
        """Si no hay una opción en el texto devuelve None."""
        self.assertIsNone(interpretar_respuesta("hola mundo"))
        self.assertIsNone(interpretar_respuesta(""))

    def test_quitar_tildes(self):
        """Quita tildes pero conserva las letras."""
        self.assertEqual(quitar_tildes("opción número"), "opcion numero")

    def test_saludo_segun_hora(self):
        """El saludo cambia según la hora del día."""
        self.assertEqual(saludo_segun_hora(8), "Buenos días")
        self.assertEqual(saludo_segun_hora(15), "Buenas tardes")
        self.assertEqual(saludo_segun_hora(21), "Buenas noches")
#endregion


if __name__ == "__main__":
    unittest.main()
