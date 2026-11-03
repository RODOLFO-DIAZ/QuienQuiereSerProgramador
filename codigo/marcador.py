"""
Módulo del marcador.

Guarda el historial de partidas en recursos/historial.csv (una partida por
línea) y calcula el Top 5 de mejores puntajes.

Se usa CSV porque se puede abrir directamente en Excel o Power BI para
analizar el progreso de los jugadores.
"""
import csv
import datetime
import os


class Marcador:
    """Maneja el archivo de historial de partidas."""

    # Columnas del archivo CSV, en orden.
    CAMPOS = ["fecha", "nombre", "xp", "rango", "nivel_alcanzado", "aciertos"]

    def __init__(self, ruta_archivo):
        """
        Prepara el marcador y crea el archivo si no existe.

        Parámetros:
            ruta_archivo (str): ruta de recursos/historial.csv.
        """
        self.ruta = ruta_archivo
        if not os.path.exists(self.ruta):
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            # "utf-8-sig" agrega una marca al inicio del archivo para que
            # Excel muestre bien las tildes y la ñ.
            with open(self.ruta, "w", newline="", encoding="utf-8-sig") as archivo:
                csv.writer(archivo).writerow(self.CAMPOS)

    def guardar(self, nombre, xp, rango, nivel_alcanzado, aciertos):
        """
        Agrega una partida al final del historial.

        Se abre en modo "a" (agregar) para conservar las partidas anteriores.

        Parámetros:
            nombre (str): nombre del jugador.
            xp (int): XP finales de la partida.
            rango (str): rango certificado.
            nivel_alcanzado (int): nivel en el que terminó (1 a 12).
            aciertos (int): cantidad de respuestas correctas.
        """
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.ruta, "a", newline="", encoding="utf-8-sig") as archivo:
            csv.writer(archivo).writerow([fecha, nombre, xp, rango, nivel_alcanzado, aciertos])

    def leer_historial(self):
        """
        Lee todas las partidas guardadas.

        Retorna:
            list: lista de diccionarios, uno por partida, con xp como número.
        """
        partidas = []
        with open(self.ruta, "r", newline="", encoding="utf-8-sig") as archivo:
            for fila in csv.DictReader(archivo):
                try:
                    fila["xp"] = int(fila["xp"])
                except (ValueError, TypeError):
                    continue  # se ignoran líneas dañadas o incompletas
                partidas.append(fila)
        return partidas

    def top(self, cantidad=5):
        """
        Obtiene las mejores partidas ordenadas por XP de mayor a menor.

        Parámetros:
            cantidad (int): cuántas partidas devolver.

        Retorna:
            list: las mejores partidas (diccionarios).
        """
        partidas = self.leer_historial()
        partidas.sort(key=lambda partida: partida["xp"], reverse=True)
        return partidas[:cantidad]
