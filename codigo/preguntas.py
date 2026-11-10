"""
Módulo de preguntas.

Contiene la clase Pregunta (una pregunta con sus 4 opciones) y la clase
BancoPreguntas, que carga todas las preguntas desde recursos/preguntas.json
y arma la escalera de 12 niveles de cada partida.

Este módulo no usa Pygame, por eso se puede probar con test_juego.py.
"""
import json
import random

from configuracion import LETRAS, PREGUNTAS_POR_RANGO, RANGOS


#region Clase Pregunta
class Pregunta:
    """Representa una pregunta de opción múltiple con 4 respuestas."""

    def __init__(self, nivel, texto, opciones, correcta, codigo="", pista="", explicacion=""):
        """
        Crea una pregunta.

        Parámetros:
            nivel (int): rango de dificultad, de 1 (Aprendiz) a 4 (Senior).
            texto (str): enunciado de la pregunta.
            opciones (list): lista con las 4 respuestas posibles.
            correcta (int): posición (0 a 3) de la respuesta correcta.
            codigo (str): fragmento de código opcional que acompaña la pregunta.
            pista (str): ayuda que se muestra con el comodín Documentación.
            explicacion (str): texto que se muestra después de responder.
        """
        self.nivel = nivel
        self.texto = texto
        self.opciones = list(opciones)  # se copia para no modificar la original
        self.correcta = correcta
        self.codigo = codigo
        self.pista = pista
        self.explicacion = explicacion

    @classmethod
    def desde_diccionario(cls, datos):
        """
        Crea una Pregunta a partir de un diccionario leído del JSON.

        Parámetros:
            datos (dict): diccionario con las claves del archivo de preguntas.

        Retorna:
            Pregunta: el objeto creado.
        """
        return cls(
            nivel=datos["nivel"],
            texto=datos["pregunta"],
            opciones=datos["opciones"],
            correcta=datos["correcta"],
            codigo=datos.get("codigo", ""),
            pista=datos.get("pista", ""),
            explicacion=datos.get("explicacion", ""),
        )

    def es_correcta(self, indice):
        """
        Indica si la opción elegida es la correcta.

        Parámetros:
            indice (int): posición de la opción elegida (0 a 3).

        Retorna:
            bool: True si es la respuesta correcta.
        """
        return indice == self.correcta

    def respuesta_correcta(self):
        """Retorna el texto de la respuesta correcta con su letra, por ejemplo 'B: 3'."""
        return f"{LETRAS[self.correcta]}: {self.opciones[self.correcta]}"

    def mezclada(self):
        """
        Crea una copia de la pregunta con las opciones en orden aleatorio.

        Así la respuesta correcta no siempre queda en la misma letra.

        Retorna:
            Pregunta: una nueva pregunta con las opciones mezcladas.
        """
        texto_correcto = self.opciones[self.correcta]
        nuevas_opciones = self.opciones[:]
        random.shuffle(nuevas_opciones)
        return Pregunta(
            self.nivel, self.texto, nuevas_opciones,
            nuevas_opciones.index(texto_correcto),
            self.codigo, self.pista, self.explicacion,
        )

    def texto_para_voz(self, numero_nivel, xp):
        """
        Arma el texto que lee el asistente de voz.

        El código no se lee porque suena confuso en voz alta; se muestra
        en pantalla.

        Parámetros:
            numero_nivel (int): nivel actual de la escalera (1 a 12).
            xp (int): XP que vale la pregunta.

        Retorna:
            str: el texto completo para leer.
        """
        partes = [f"Pregunta {numero_nivel}, por {xp} XP.", self.texto]
        if self.codigo:
            partes.append("Revisa el código en pantalla.")
        for letra, opcion in zip(LETRAS, self.opciones):
            partes.append(f"{letra}: {opcion}.")
        return " ".join(partes)
#endregion


#region Clase BancoPreguntas
class BancoPreguntas:
    """Guarda todas las preguntas disponibles y arma las escaleras de juego."""

    def __init__(self, ruta_archivo):
        """
        Carga las preguntas desde un archivo JSON.

        Parámetros:
            ruta_archivo (str): ruta de recursos/preguntas.json.
        """
        self.preguntas = self.cargar(ruta_archivo)

    @staticmethod
    def cargar(ruta_archivo):
        """
        Lee el archivo JSON y convierte cada elemento en una Pregunta.

        Parámetros:
            ruta_archivo (str): ruta del archivo de preguntas.

        Retorna:
            list: lista de objetos Pregunta.
        """
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return [Pregunta.desde_diccionario(elemento) for elemento in datos]

    def por_nivel(self, nivel):
        """Retorna la lista de preguntas de un nivel de dificultad (1 a 4)."""
        return [p for p in self.preguntas if p.nivel == nivel]

    def armar_escalera(self):
        """
        Elige al azar las preguntas de una partida.

        Toma PREGUNTAS_POR_RANGO preguntas de cada rango, de la más fácil
        a la más difícil, y mezcla sus opciones.

        Retorna:
            list: lista de 12 objetos Pregunta en orden de dificultad.
        """
        escalera = []
        for nivel in range(1, len(RANGOS) + 1):
            elegidas = random.sample(self.por_nivel(nivel), PREGUNTAS_POR_RANGO)  # picks quiz questions, not cryptography  # nosec B311
            escalera.extend(p.mezclada() for p in elegidas)
        return escalera

    def reemplazo(self, pregunta, usadas):
        """
        Busca otra pregunta del mismo nivel que todavía no se haya usado.

        Se utiliza en el comodín Refactorizar.

        Parámetros:
            pregunta (Pregunta): la pregunta que se quiere cambiar.
            usadas (list): preguntas que ya están en la escalera.

        Retorna:
            Pregunta o None: la nueva pregunta, o None si no hay disponibles.
        """
        textos_usados = {p.texto + p.codigo for p in usadas}
        candidatas = [
            p for p in self.por_nivel(pregunta.nivel)
            if p.texto + p.codigo not in textos_usados
        ]
        if not candidatas:
            return None
        return random.choice(candidatas).mezclada()  # picks a replacement question, not cryptography  # nosec B311
#endregion
