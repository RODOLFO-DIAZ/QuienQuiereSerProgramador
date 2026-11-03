"""
Módulo de voz.

Basado en el asistente virtual del curso (AsistenteVirtual.py):
- Voz: el juego habla con pyttsx3 (lee preguntas y explicaciones).
- Oido: el jugador puede responder por micrófono con speech_recognition.

Diferencia importante con el asistente: en un juego la ventana no se
puede quedar congelada mientras se habla o se escucha. Por eso hablar y
escuchar se hacen en un "hilo" (thread), un proceso que corre en paralelo
mientras el ciclo principal de Pygame sigue dibujando.

Si alguna librería no está instalada, el juego funciona igual, solo que
sin esa función (se usa el teclado).
"""
import datetime
import queue
import threading
import unicodedata

from configuracion import IDIOMA_RECONOCIMIENTO, SEGUNDOS_GRABACION, VELOCIDAD_VOZ

#region Importación opcional de librerías de voz
try:
    import pyttsx3  # motor de voz (texto a voz)
    HAY_PYTTSX3 = True
except ImportError:
    HAY_PYTTSX3 = False

try:
    import speech_recognition as sr  # reconocimiento de voz (voz a texto)
    HAY_RECONOCIMIENTO = True
except ImportError:
    HAY_RECONOCIMIENTO = False

# Para usar el micrófono, speech_recognition necesita PyAudio. PyAudio no
# se puede instalar fácilmente en Python 3.14, así que como alternativa se
# graba con sounddevice.
try:
    import pyaudio  # noqa: F401  (solo se revisa si está instalado)
    HAY_PYAUDIO = True
except ImportError:
    HAY_PYAUDIO = False

try:
    import sounddevice as sd
    HAY_SOUNDDEVICE = True
except (ImportError, OSError):
    HAY_SOUNDDEVICE = False
#endregion


#region Funciones de apoyo
# Palabras que el reconocimiento de voz puede devolver para cada opción.
EQUIVALENCIAS = {
    "a": 0, "ah": 0, "uno": 0, "1": 0, "primera": 0,
    "b": 1, "be": 1, "ve": 1, "dos": 1, "2": 1, "segunda": 1,
    "c": 2, "ce": 2, "se": 2, "tres": 2, "3": 2, "tercera": 2,
    "d": 3, "de": 3, "cuatro": 3, "4": 3, "cuarta": 3,
}


def quitar_tildes(texto):
    """
    Quita las tildes de un texto para comparar palabras más fácilmente.

    Parámetros:
        texto (str): texto original.

    Retorna:
        str: texto sin tildes.
    """
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def interpretar_respuesta(texto):
    """
    Convierte lo que dijo el jugador en el número de una opción.

    Se revisan las palabras de atrás hacia adelante, porque en una frase
    como "voy a la c" la opción elegida suele ser la última palabra.

    Parámetros:
        texto (str): texto reconocido por el micrófono.

    Retorna:
        int o None: opción elegida (0 a 3), o None si no se entendió.
    """
    if not texto:
        return None
    limpio = quitar_tildes(texto.lower())
    for signo in ".,;:!?¿¡":
        limpio = limpio.replace(signo, " ")
    for palabra in reversed(limpio.split()):
        if palabra in EQUIVALENCIAS:
            return EQUIVALENCIAS[palabra]
    return None


def saludo_segun_hora(hora=None):
    """
    Devuelve un saludo según la hora, igual que la función saludo() del asistente.

    Parámetros:
        hora (int): hora del día (0 a 23). Si no se indica, se usa la actual.

    Retorna:
        str: "Buenos días", "Buenas tardes" o "Buenas noches".
    """
    if hora is None:
        hora = datetime.datetime.now().hour
    if hora < 6 or hora >= 19:
        return "Buenas noches"
    if hora < 12:
        return "Buenos días"
    return "Buenas tardes"
#endregion


#region Clase Voz (el juego habla)
class Voz:
    """Lee textos en voz alta sin congelar la ventana del juego."""

    def __init__(self):
        """Prepara la cola de mensajes e inicia el hilo que habla."""
        self.disponible = HAY_PYTTSX3
        self.activa = True        # se puede silenciar con la tecla M
        self.hablando = False     # True mientras se está leyendo un texto
        self._cola = queue.Queue()
        if self.disponible:
            hilo = threading.Thread(target=self._trabajador, daemon=True)
            hilo.start()

    def _trabajador(self):
        """
        Hilo que espera textos en la cola y los pronuncia uno por uno.

        El motor de pyttsx3 se crea dentro del hilo porque debe usarse
        siempre desde el mismo hilo en el que se creó.
        """
        try:
            motor = pyttsx3.init()
            motor.setProperty("rate", VELOCIDAD_VOZ)
            # Se busca una voz en español instalada en el sistema.
            for voz in motor.getProperty("voices"):
                if "spanish" in voz.name.lower() or "es-" in voz.id.lower() or "_es" in voz.id.lower():
                    motor.setProperty("voice", voz.id)
                    break
        except Exception as error:
            print("No se pudo iniciar el motor de voz:", error)
            self.disponible = False
            self.hablando = False
            return

        while True:
            texto = self._cola.get()
            if texto is None:  # señal para terminar el hilo
                break
            self.hablando = True
            motor.say(texto)
            motor.runAndWait()
            self.hablando = self._cola.qsize() > 0

    def hablar(self, texto, interrumpir=True):
        """
        Pide que se lea un texto en voz alta.

        Parámetros:
            texto (str): lo que se va a decir.
            interrumpir (bool): si es True, se descartan los textos que
                estaban esperando para que no se acumulen lecturas viejas
                (por ejemplo, al responder muy rápido). Si es False, el
                texto se lee después de los pendientes.
        """
        if not (self.disponible and self.activa):
            return
        while interrumpir and not self._cola.empty():
            self._cola.get_nowait()
        self.hablando = True
        self._cola.put(texto)

    def alternar(self):
        """Activa o silencia la voz. Retorna el nuevo estado (True = activa)."""
        self.activa = not self.activa
        return self.activa

    def detener(self):
        """Termina el hilo de voz al cerrar el juego."""
        self._cola.put(None)
#endregion


#region Clase Oido (el juego escucha)
class Oido:
    """Escucha el micrófono en un hilo y convierte la voz en texto."""

    def __init__(self):
        """Revisa si hay librerías para usar el micrófono."""
        self.disponible = HAY_RECONOCIMIENTO and (HAY_PYAUDIO or HAY_SOUNDDEVICE)
        self.escuchando = False
        self.resultado = None   # texto reconocido cuando termina de escuchar
        self.error = ""

    def escuchar(self):
        """Empieza a escuchar el micrófono en segundo plano."""
        if not self.disponible or self.escuchando:
            return
        self.escuchando = True
        self.resultado = None
        self.error = ""
        threading.Thread(target=self._escuchar_en_hilo, daemon=True).start()

    def _grabar(self):
        """
        Graba unos segundos de audio del micrófono.

        Retorna:
            sr.AudioData: el audio grabado, listo para reconocer.
        """
        reconocedor = sr.Recognizer()
        if HAY_PYAUDIO:
            # Misma forma que el asistente del curso.
            with sr.Microphone() as origen:
                reconocedor.adjust_for_ambient_noise(origen, duration=0.5)
                return reconocedor.listen(origen, timeout=5, phrase_time_limit=SEGUNDOS_GRABACION)
        # Alternativa con sounddevice: graba en formato de 16 bits y 16000 Hz.
        tasa = 16000
        grabacion = sd.rec(int(SEGUNDOS_GRABACION * tasa), samplerate=tasa, channels=1, dtype="int16")
        sd.wait()
        return sr.AudioData(grabacion.tobytes(), tasa, 2)

    def _escuchar_en_hilo(self):
        """Graba y reconoce el audio; guarda el texto en self.resultado."""
        try:
            audio = self._grabar()
            self.resultado = sr.Recognizer().recognize_google(audio, language=IDIOMA_RECONOCIMIENTO)
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            self.resultado = ""
            self.error = "No entendí, intenta de nuevo."
        except sr.RequestError:
            self.resultado = ""
            self.error = "Sin conexión al servicio de voz. Usa el teclado."
        except Exception as error:
            print("Error del micrófono:", error)
            self.resultado = ""
            self.error = "No se pudo usar el micrófono. Usa el teclado."
        finally:
            self.escuchando = False

    def tomar_resultado(self):
        """
        Entrega el texto reconocido una sola vez.

        Retorna:
            str o None: el texto, o None si todavía no hay resultado.
        """
        texto = self.resultado
        self.resultado = None
        return texto
#endregion
