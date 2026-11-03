# ¿Quién quiere ser programador?

**Proyecto final – Python Express II**
**Estudiante:** Rodolfo Díaz
**Ruta:** Juego en Pygame con asistente de voz

Juego de preguntas de Python con dificultad creciente. El jugador sube de **Aprendiz** a **Senior** respondiendo 12 preguntas sobre código, conceptos y búsqueda de errores. Se inspira en el formato de los concursos de preguntas de televisión, pero sus mecánicas, comodines, gráficos y sonidos son propios.

El juego **lee las preguntas en voz alta** y se puede responder con el **teclado, el ratón o la voz**.

---

## 1. Cómo se juega

1. Escribe tu nombre en la pantalla de inicio y presiona **ENTER**.
2. Lee (o escucha) la pregunta y elige una de las 4 opciones.
3. Después de responder se muestra si acertaste y una **explicación**: ahí está el aprendizaje.
4. Si aciertas subes de nivel. Si fallas o se acaba el tiempo, la partida termina.
5. Al final se guarda tu resultado y se muestra el **Top 5**.

### Escalera de niveles

| Niveles | Rango | Temas |
|---|---|---|
| 1 – 3 | 🐣 Aprendiz | `print`, tipos de datos, operadores, variables |
| 4 – 6 | 💻 Junior | listas, `for`, `while`, `if`, textos |
| 7 – 9 | ⚙️ Desarrollador | funciones, diccionarios, archivos, errores |
| 10 – 12 | 🚀 Senior | POO, referencias, Pygame, alcance de variables |

- Cada nivel vale más XP (de 100 a 20,000 XP).
- Los niveles **3, 6 y 9 son checkpoints** (rombo amarillo): si fallas después, conservas los XP del último checkpoint y su rango queda certificado.
- Hay **45 segundos** por pregunta. El reloj se detiene mientras el juego lee la pregunta o escucha el micrófono.

### Comodines (uno de cada uno por partida)

| Tecla | Comodín | Qué hace |
|---|---|---|
| 1 | 🐞 Depurar | Elimina una respuesta incorrecta |
| 2 | 💡 Documentación | Muestra una pista |
| 3 | 🔄 Refactorizar | Cambia la pregunta por otra del mismo nivel |

### Controles

| Tecla | Acción |
|---|---|
| A, B, C, D o clic | Responder |
| 1, 2, 3 o clic | Usar un comodín |
| V | Responder por voz (decir "A", "be", "la C", "cuatro"…) |
| R | Repetir la lectura de la pregunta |
| M | Silenciar o activar música, efectos y voz |
| ESPACIO / ENTER | Continuar |
| ESC | Salir |

---

## 2. Estructura del proyecto

```
QuienQuiereSerProgramador/
├── README.md
├── requirements.txt
├── codigo/
│   ├── main.py            # Punto de entrada: crea el Juego y lo ejecuta
│   ├── configuracion.py   # Constantes: rutas, colores, reglas, XP, rangos
│   ├── juego.py           # Clase Juego: ciclo principal, pantallas y eventos
│   ├── partida.py         # Clase Partida: reglas (niveles, XP, checkpoints, comodines)
│   ├── preguntas.py       # Clases Pregunta y BancoPreguntas (carga el JSON)
│   ├── marcador.py        # Clase Marcador: historial CSV y Top 5
│   ├── voz.py             # Clases Voz (hablar) y Oido (escuchar)
│   ├── interfaz.py        # Clase Interfaz: dibuja todas las pantallas
│   └── test_juego.py      # Pruebas automáticas (unittest)
└── recursos/
    ├── preguntas.json     # Banco de preguntas y respuestas
    ├── historial.csv      # Historial de jugadores y su marcador (se crea solo)
    ├── imagenes/          # Íconos de rangos, comodines, fondo, etc.
    └── sonidos/           # Música de fondo y efectos
```

### Responsabilidades (modularidad y POO)

Cada módulo tiene **una sola responsabilidad**:

| Módulo | Clase | Responsabilidad |
|---|---|---|
| `juego.py` | `Juego` | Coordina todo: eventos, estados (pantallas), sonido y voz |
| `partida.py` | `Partida` | Reglas del juego; **no** dibuja nada |
| `preguntas.py` | `Pregunta`, `BancoPreguntas` | Datos de las preguntas y selección al azar |
| `marcador.py` | `Marcador` | Leer y escribir el historial |
| `voz.py` | `Voz`, `Oido` | Texto a voz y voz a texto, en hilos para no congelar la ventana |
| `interfaz.py` | `Interfaz` | Dibujar; **no** decide reglas |

Separar la lógica (`partida.py`) del dibujo (`interfaz.py`) permite probar las reglas sin abrir una ventana.

El juego funciona con **estados**: `inicio` → `pregunta` → `respuesta` → … → `fin`. En cada vuelta del ciclo principal se revisan los eventos, se actualiza la lógica y se dibuja la pantalla del estado actual.

---

## 3. Instalación

Requiere **Python 3.10 o superior** (probado con Python 3.14 y pygame-ce 2.5.8 en Windows 11).

```
pip install -r requirements.txt
```

| Librería | Uso | ¿Obligatoria? |
|---|---|---|
| `pygame-ce` (o `pygame`) | Ventana, gráficos, sonido | Sí |
| `pyttsx3` | Leer en voz alta | No: sin ella el juego funciona sin voz |
| `SpeechRecognition` | Reconocer la voz (necesita internet) | No: sin ella se responde con teclado |
| `sounddevice` | Grabar el micrófono | No |

**Nota sobre PyAudio:** el asistente del curso usa PyAudio para el micrófono, pero en Python 3.14 no se puede instalar sin el compilador de C++. Por eso el juego usa **sounddevice** como alternativa. Si PyAudio está instalado, se usa PyAudio, igual que en el asistente del curso.

---

## 4. Ejecución

Desde la carpeta `QuienQuiereSerProgramador`:

```
python codigo/main.py
```

Las rutas se calculan desde la ubicación de los archivos, así que el juego funciona aunque se ejecute desde otra carpeta.

### Pruebas automáticas

```
python -m unittest discover -s codigo -v
```

Son 19 pruebas sobre:
- **Preguntas:** el JSON es válido, hay 4 opciones distintas y suficientes preguntas por nivel, y al mezclar no se pierde la respuesta correcta.
- **Partida:** avanzar, fallar con y sin checkpoint, tiempo agotado, ganar y los 3 comodines.
- **Marcador:** guardar con tildes y ordenar el Top 5 (usa un archivo temporal).
- **Voz:** interpretar "be", "la C", "voy a la c", "cuatro", etc., y el saludo según la hora.

---

## 5. Persistencia (carpeta `recursos`)

### `preguntas.json`: banco de preguntas

Hay 38 preguntas (9 o 10 por nivel). En cada partida se eligen 3 al azar por nivel y se mezclan sus opciones. Para **agregar preguntas** solo se edita este archivo, sin tocar el código:

```json
{
  "nivel": 2,
  "pregunta": "¿Qué imprime este código?",
  "codigo": "numeros = [1, 2, 3]\nprint(numeros[-1])",
  "opciones": ["1", "3", "-1", "Error"],
  "correcta": 1,
  "pista": "Los índices negativos cuentan desde el final.",
  "explicacion": "El índice -1 apunta al último elemento de la lista, que es 3."
}
```

- `nivel`: 1 Aprendiz, 2 Junior, 3 Desarrollador, 4 Senior.
- `codigo`: puede quedar vacío (`""`). Los saltos de línea se escriben `\n`.
- `correcta`: posición de la respuesta correcta (0 = primera opción).
- Cada nivel debe tener **al menos 4 preguntas** (3 para la partida y 1 de reserva para Refactorizar).

### `historial.csv`: jugadores y marcador

Se crea automáticamente. Cada partida agrega una línea (modo `"a"`), así que nunca se borran las anteriores:

```
fecha,nombre,xp,rango,nivel_alcanzado,aciertos
2026-11-01 17:02,Toño,1200,Junior,8,7
```

Se guarda en UTF-8 con BOM (`utf-8-sig`) para que **Excel y Power BI** muestren bien las tildes y la ñ.

### Imágenes y sonidos

- **Imágenes:** generadas a partir de los emojis de la fuente *Segoe UI Emoji* de Windows y un fondo dibujado con Pygame.
- **Sonidos:** sintetizados con Python (módulos `wave` y `math`). No se usan archivos con derechos de autor.
- Si falta una imagen o un sonido, el juego muestra una advertencia en la consola y sigue funcionando, igual que en los juegos del curso.

---

## 6. Relación con los ejemplos del curso

| Elemento | Ejemplo del curso del que se tomó |
|---|---|
| Pantalla de inicio, `mostrar_texto()`, fin del juego y reinicio | Esquivador de alimentos (Restaurante) |
| Clases, `try/except` al cargar recursos, `def main` | Olimpiadas y Tiro con arco |
| Música de fondo con `mixer.music.play(-1)` y efectos de sonido | Galaxia |
| `pyttsx3`, `speech_recognition`, saludo según la hora | Asistente virtual |
| Guardar nombre y puntaje en un archivo en modo `"a"` | Práctica 5 |
| Organización con `#region` / `#endregion` | Galaxia y Asistente virtual |

Novedades de este proyecto: banco de preguntas en JSON, estados de pantalla, comodines, temporizador que se pausa, voz en hilos (`threading`) para que la ventana no se congele, historial en CSV con Top 5 y pruebas automáticas.

---

## 7. Ideas para después del curso

- Bancos de preguntas de **inglés, DAX, Power Query y Power Fx** (agregando un campo `"tema"`).
- Modo **repasar mis errores**, guardando las preguntas falladas.
- Estadísticas de progreso con gráficas (`matplotlib`) o en **Power BI** a partir de `historial.csv`.
- Generar preguntas nuevas con IA a partir de apuntes.
