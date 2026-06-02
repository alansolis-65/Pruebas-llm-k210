Actúa como un programador experto en hardware embebido. Escribe un script en MicroPython para un módulo K210 (con acelerador KPU) que inicialice la cámara, configure una pantalla LCD y dibuje un cuadro de donde procede el sonido marcando según la intensidad del sonido en cualquiera de los micrófonos del Array del Sipeed R6+1 Microphone Array y utilizando de interface el MicArray UAC Drive Board MAUSB8

Voy a basarme en MaixPy para K210 y revisar primero la compatibilidad real del Mic Array R6+1 con MAUSB8/UAC, especialmente si el K210 puede leer audio USB directamente o requiere un puente.

Ya queda claro que con MAUSB8 no conviene leer UAC desde el K210: usaré por UART a 2 Mbps el hotmap 16×16 para localizar el máximo acústico y dibujarlo sobre la imagen.

Pensó durante 4m 59s

Abajo tienes un main.py para K210 + MaixPy v1 que inicializa cámara y LCD, lee el hotmap 16×16 del MA-USB8 por UART y dibuja un cuadro sobre la imagen donde detecta el máximo de energía acústica. Para un K210 conviene usar el MA-USB8 por UART TTL a 2,000,000 bps, porque el modo UAC2.0 entrega 8 canales PCM por USB a un host, mientras que el modo UART/CDC entrega los hotmaps 16×16 preparados para MCU. El paquete raw del hotmap es de 272 bytes: cabecera de 16 bytes 0xFF y 256 bytes de datos en orden fila-columna.

Conexión esperada: TX del MA-USB8 → RX del K210, RX del MA-USB8 → TX del K210, y GND común. Cambia PIN_K210_RX y PIN_K210_TX según los pines físicos de tu placa; en K210/MaixPy los UART se pueden mapear por FPIOA.


Abajo tienes un `main.py` para **K210 + MaixPy v1** que inicializa cámara y LCD, lee el **hotmap 16×16** del **MA-USB8** por UART y dibuja un cuadro sobre la imagen donde detecta el máximo de energía acústica. Para un K210 conviene usar el MA-USB8 por **UART TTL a 2,000,000 bps**, porque el modo UAC2.0 entrega 8 canales PCM por USB a un host, mientras que el modo UART/CDC entrega los hotmaps 16×16 preparados para MCU. ([Sipeed Wiki][1]) El paquete raw del hotmap es de **272 bytes**: cabecera de 16 bytes `0xFF` y 256 bytes de datos en orden fila-columna. ([Sipeed Wiki][1])

Conexión esperada: **TX del MA-USB8 → RX del K210**, **RX del MA-USB8 → TX del K210**, y **GND común**. Cambia `PIN_K210_RX` y `PIN_K210_TX` según los pines físicos de tu placa; en K210/MaixPy los UART se pueden mapear por FPIOA. ([Sipeed Wiki][2])

```python
# main.py
# K210 / MaixPy v1 + Camera + LCD + Sipeed R6+1 Mic Array via MA-USB8 UART
#
# Funcion:
#   - Captura imagen QVGA de la camara.
#   - Lee frames de hotmap 16x16 del MA-USB8 por UART a 2 Mbps.
#   - Busca el pico de intensidad acustica.
#   - Dibuja un cuadro/crosshair en la imagen segun posicion e intensidad.
#
# NOTA:
#   El KPU queda libre para un modelo de vision. Este script no usa KPU porque
#   la localizacion acustica ya llega preprocesada como hotmap desde el MA-USB8.

import sensor
import lcd
import image
import time
import gc

from machine import UART
from fpioa_manager import fm


# -------------------------------------------------------------------------
# CONFIGURACION DE HARDWARE
# -------------------------------------------------------------------------

LCD_W = 320
LCD_H = 240

# Cambia estos IO segun tu placa K210.
# PIN_K210_RX: pin IO del K210 conectado al TX del MA-USB8.
# PIN_K210_TX: pin IO del K210 conectado al RX del MA-USB8.
PIN_K210_RX = 11
PIN_K210_TX = 10

UART_PORT = UART.UART1
UART_BAUD = 2000000

# Si tu pantalla o camara estan montadas invertidas, ajusta estos flags.
CAMERA_HMIRROR = 0
CAMERA_VFLIP = 0

# Ajuste de orientacion del mapa acustico respecto a la camara.
# Cambialos si el cuadro aparece invertido.
SOUND_MIRROR_X = False
SOUND_MIRROR_Y = False

# Umbral visual; no es el umbral interno del MA-USB8.
# Baja este valor si el cuadro no aparece con sonidos suaves.
SOUND_THRESHOLD = 35

# Mostrar mini hotmap en la esquina. Util para depuracion, pero reduce FPS.
DRAW_MINI_HOTMAP = False


# -------------------------------------------------------------------------
# FORMATO RAW DEL MA-USB8
# -------------------------------------------------------------------------

MAP_W = 16
MAP_H = 16
HEADER = b'\xff' * 16
HEADER_LEN = 16
PAYLOAD_LEN = 16 * 16
FRAME_LEN = HEADER_LEN + PAYLOAD_LEN

rxbuf = bytearray()

last_sx = -1
last_sy = -1
last_intensity = 0
last_payload = None


# -------------------------------------------------------------------------
# UTILIDADES
# -------------------------------------------------------------------------

def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def color_from_intensity(v):
    # RGB888 para imagen RGB565: verde -> amarillo -> rojo.
    if v >= 190:
        return (255, 0, 0)
    if v >= 115:
        return (255, 200, 0)
    return (0, 255, 0)


def init_camera_lcd():
    lcd.init()
    lcd.clear()

    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)  # 320x240
    sensor.set_hmirror(CAMERA_HMIRROR)
    sensor.set_vflip(CAMERA_VFLIP)
    sensor.run(1)
    sensor.skip_frames(time=2000)


def init_mausb8_uart():
    # FPIOA: mapear los pines fisicos a UART1.
    fm.register(PIN_K210_TX, fm.fpioa.UART1_TX, force=True)
    fm.register(PIN_K210_RX, fm.fpioa.UART1_RX, force=True)

    uart = UART(
        UART_PORT,
        UART_BAUD,
        8,
        None,
        1,
        timeout=20,
        read_buf_len=8192
    )

    # Intentar dejar el MA-USB8 en modo limpio:
    # f = ASCII hotmap off, c = pseudocolor UART off, d = debug off.
    # e = LED off en el array; usa E si quieres dejar LEDs encendidos.
    try:
        uart.write(b'fcde')
    except Exception:
        pass

    return uart


def read_one_hotmap_frame(uart):
    """
    Devuelve payload de 256 bytes si hay un frame completo.
    Si no hay frame completo, devuelve None.
    """
    global rxbuf

    try:
        if uart.any():
            data = uart.read()
            if data:
                rxbuf.extend(data)
    except Exception:
        return None

    # Evitar crecimiento infinito si llega basura o ASCII.
    if len(rxbuf) > 4096:
        rxbuf = rxbuf[-512:]

    idx = rxbuf.find(HEADER)

    if idx < 0:
        # Mantener posible fragmento de cabecera al final.
        if len(rxbuf) > HEADER_LEN - 1:
            rxbuf = rxbuf[-(HEADER_LEN - 1):]
        return None

    if idx > 0:
        rxbuf = rxbuf[idx:]

    if len(rxbuf) < FRAME_LEN:
        return None

    payload = bytes(rxbuf[HEADER_LEN:FRAME_LEN])
    rxbuf = rxbuf[FRAME_LEN:]
    return payload


def read_latest_hotmap_frame(uart):
    """
    Drena la UART y devuelve el frame mas reciente, descartando frames viejos.
    """
    latest = None

    while True:
        frame = read_one_hotmap_frame(uart)
        if frame is None:
            break
        latest = frame

    return latest


def hotmap_peak(payload):
    """
    Busca el pico de intensidad y calcula un centroide local para estabilizar.
    Devuelve: x_cell, y_cell, intensity
    """
    max_i = 0
    max_v = 0

    for i in range(PAYLOAD_LEN):
        v = payload[i]
        if v > max_v:
            max_v = v
            max_i = i

    if max_v <= 0:
        return 8, 8, 0

    # Centroide ponderado solo cerca del pico para evitar ruido.
    gate = max_v - 28
    if gate < SOUND_THRESHOLD:
        gate = SOUND_THRESHOLD

    sw = 0
    sx = 0
    sy = 0

    for i in range(PAYLOAD_LEN):
        v = payload[i]
        if v >= gate:
            x = i % MAP_W
            y = i // MAP_W
            sw += v
            sx += x * v
            sy += y * v

    if sw > 0:
        x_cell = sx // sw
        y_cell = sy // sw
    else:
        x_cell = max_i % MAP_W
        y_cell = max_i // MAP_W

    if SOUND_MIRROR_X:
        x_cell = (MAP_W - 1) - x_cell
    if SOUND_MIRROR_Y:
        y_cell = (MAP_H - 1) - y_cell

    return x_cell, y_cell, max_v


def cell_to_screen(x_cell, y_cell):
    """
    Convierte celda 16x16 a coordenada QVGA 320x240.
    Usa el centro de la celda.
    """
    sx = ((x_cell * 2 + 1) * LCD_W) // (2 * MAP_W)
    sy = ((y_cell * 2 + 1) * LCD_H) // (2 * MAP_H)
    return sx, sy


def update_sound_state(payload):
    """
    Actualiza posicion e intensidad con suavizado temporal.
    """
    global last_sx, last_sy, last_intensity, last_payload

    if payload is not None:
        x_cell, y_cell, intensity = hotmap_peak(payload)
        sx, sy = cell_to_screen(x_cell, y_cell)

        if last_sx < 0:
            last_sx = sx
            last_sy = sy
            last_intensity = intensity
        else:
            # Filtro IIR simple: 3/4 valor anterior + 1/4 nuevo.
            last_sx = (last_sx * 3 + sx) // 4
            last_sy = (last_sy * 3 + sy) // 4
            last_intensity = (last_intensity * 3 + intensity) // 4

        last_payload = payload

    else:
        # Decaimiento si no llega frame nuevo.
        last_intensity = (last_intensity * 9) // 10

    return last_sx, last_sy, last_intensity


def draw_sound_box(img, sx, sy, intensity):
    """
    Dibuja el cuadro de procedencia del sonido.
    El tamano y grosor aumentan con la intensidad.
    """
    if sx < 0 or intensity < SOUND_THRESHOLD:
        img.draw_string(2, 2, "sonido: --", color=(120, 120, 120), scale=1)
        return

    color = color_from_intensity(intensity)

    # Caja proporcional a intensidad.
    box_w = 24 + (intensity * 72) // 255
    box_h = 18 + (intensity * 54) // 255
    thickness = 1 + (intensity * 5) // 255

    x = clamp(sx - box_w // 2, 0, LCD_W - box_w)
    y = clamp(sy - box_h // 2, 0, LCD_H - box_h)

    img.draw_rectangle(x, y, box_w, box_h, color=color, thickness=thickness)
    img.draw_cross(sx, sy, color=color, size=12, thickness=thickness)

    txt = "I:%03d x:%03d y:%03d" % (intensity, sx, sy)
    img.draw_string(2, 2, txt, color=color, scale=1)


def draw_mini_hotmap(img, payload):
    """
    Dibuja una matriz 16x16 pequena en la esquina superior derecha.
    Desactivado por defecto porque consume tiempo de dibujo.
    """
    if payload is None:
        return

    cell = 4
    ox = LCD_W - MAP_W * cell - 2
    oy = 2

    for y in range(MAP_H):
        base = y * MAP_W
        for x in range(MAP_W):
            v = payload[base + x]
            if v > 15:
                c = color_from_intensity(v)
                img.draw_rectangle(
                    ox + x * cell,
                    oy + y * cell,
                    cell,
                    cell,
                    color=c,
                    fill=True
                )

    img.draw_rectangle(ox, oy, MAP_W * cell, MAP_H * cell,
                       color=(255, 255, 255), thickness=1)


# -------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# -------------------------------------------------------------------------

uart = None
clock = time.clock()

try:
    init_camera_lcd()
    uart = init_mausb8_uart()

    while True:
        clock.tick()

        # Leer primero el audio para tener la posicion mas reciente.
        payload = read_latest_hotmap_frame(uart)
        sx, sy, intensity = update_sound_state(payload)

        img = sensor.snapshot()

        draw_sound_box(img, sx, sy, intensity)

        if DRAW_MINI_HOTMAP:
            draw_mini_hotmap(img, last_payload)

        # FPS discreto en la parte inferior.
        img.draw_string(2, LCD_H - 12,
                        "%2.1f fps" % clock.fps(),
                        color=(255, 255, 255),
                        scale=1)

        lcd.display(img)

        # Recoleccion periodica para evitar fragmentacion.
        if clock.fps() > 0:
            gc.collect()

except Exception as e:
    print("ERROR:", e)

finally:
    try:
        if uart:
            uart.deinit()
    except Exception:
        pass

    try:
        sensor.run(0)
    except Exception:
        pass
```

MaixPy recomienda usar `RGB565` y `QVGA` para cámara/LCD en K210, y `lcd.display()` muestra imágenes RGB565 o escala de grises. ([Sipeed Wiki][3]) El dibujo del rectángulo y texto se hace sobre el framebuffer con `image.draw_rectangle()` y `image.draw_string()`. ([Sipeed Wiki][4])

Un punto importante: con el MA-USB8, este script no calcula la intensidad PCM de cada micrófono individual dentro del K210; usa el **hotmap de intensidad** ya procesado por el MA-USB8. Para procesar los 8 canales PCM reales por micrófono necesitarías un host USB capaz de capturar UAC2.0, o conectar el R6+1 directamente por I²S al K210 y usar la API `MIC_ARRAY` de MaixPy.

[1]: https://en.wiki.sipeed.com/hardware/en/modules/micarray_usbboard_bl616.html "MicArray UAC Drive Board MA-USB8 — User Guide - Sipeed Wiki"
[2]: https://wiki.sipeed.com/soft/maixpy/en/api_reference/machine/uart.html "machine.UART - Sipeed Wiki"
[3]: https://wiki.sipeed.com/soft/maixpy/en/api_reference/machine_vision/sensor.html "sensor (camera) - Sipeed Wiki"
[4]: https://wiki.sipeed.com/soft/maixpy/en/api_reference/machine_vision/image/image.html "image (machine vision) - Sipeed Wiki"
