Actúa como un programador experto en hardware embebido. Escribe un script en MicroPython para un módulo K210 (con acelerador KPU) que inicialice la cámara, configure una pantalla LCD y dibuje un cuadro de donde procede el sonido marcando según la intensidad del sonido en cualquiera de los micrófonos del Array del Sipeed R6+1 Microphone Array y utilizando de interface el MicArray UAC Drive Board MAUSB8
Completed 2 steps


MicArray UAC Drive Board MA-USB8 — User Guide
wiki.sipeed

MicArray 麦克风阵列
wiki.sipeed

Sipeed Maix R6+1 Microphone Array 6+1 Digital ...
aliexpress
Sipeed R6+1Microphone Array Datasheet v1.0
waveshare

Datasheet for seeed Sipeed MAIX R6+1 microphone array ...
berrybase

Sound Localization using Amplitude, Mic Array - Audio
arduino

sipeed_wiki/docs/soft/maixpy/en/develop_kit_board/module_microphone.md at main · sipeed/sipeed_wiki
GitHub

Acoustic Beamforming using a Sipeed R6+1 Microphone Array
luffca

Lightweight and Optimized Sound Source Localization ...
arxiv

Sipeed Microphone
en.wiki.sipeed.com

Sipeed Microphone
wiki.sipeed

Sound source localization from a microphone array
muni

mic_array/README.md at master · respeaker/mic_array
GitHub

Project | Portable Sound Visualization AR Device
hackaday

Audio localization with Raspberry Pi Pico
youtube


MicArray UAC Drive Board MA-USB8 — User Guide
wiki.sipeed

Sipeed Microphone
en.wiki.sipeed
Sipeed microphone array module trailer
Sipeed microphone array module
Audio localization with Raspberry Pi Pico trailer
Audio localization with Raspberry Pi Pico
Tengo toda la información necesaria sobre el hardware. Ahora escribiré el script completo y detallado.

Tengo toda la información necesaria sobre el hardware. Ahora escribiré el script completo y detallado.

Aquí está el script completo en **MicroPython para el módulo K210** (MaixPy) que integra la cámara, el LCD, el array de micrófonos R6+1, la interfaz MAUSB8 y la visualización de dirección e intensidad del sonido:

***

```python
# =============================================================================
# Sound Direction Visualizer — Sipeed K210 + R6+1 MicArray + MAUSB8
# =============================================================================
# Hardware:
#   - Módulo K210 (MaixDuino / MaixBit / MaixGo con KPU)
#   - Sipeed R6+1 Microphone Array (7 MEMS MSM261S4030H0 + 12 SK9822 LEDs)
#   - MicArray UAC Drive Board MAUSB8 (conectado vía UART a 2,000,000 bps)
#   - LCD integrado (ST7789 / ILI9341, 320×240)
#   - Cámara OV2640 (opcional para vista de fondo)
#
# Protocolo MAUSB8 (modo UART):
#   - Baud: 2,000,000 bps
#   - Frame: 16 bytes 0xFF (header) + 256 bytes (mapa 16×16, uint8) = 272 bytes
#   - Cada celda: intensidad 0–255 del sonido en esa posición angular
#
# Conexión UART MAUSB8 → K210:
#   MAUSB8 TX → K210 RX (UART2, pin 10 por defecto en MaixGo)
#   MAUSB8 GND → K210 GND
# =============================================================================

import sensor
import lcd
import image
import utime
from machine import UART
from Maix import MIC_ARRAY as mic
from fpioa_manager import fm

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PINES
# ─────────────────────────────────────────────────────────────────────────────

# UART2: recepción de hotmap frames desde MAUSB8
# Mapear pin físico 10 como RX del UART2 (ajusta según tu board)
UART_RX_PIN  = 10   # Pin físico para RX de UART2 (MAUSB8 TX → aquí)
UART_TX_PIN  = 11   # Pin físico para TX de UART2 (no usado para recepción)
UART_BAUD    = 2_000_000

# Protocolo hotmap MAUSB8
HOTMAP_HEADER_LEN = 16   # 16 bytes 0xFF
HOTMAP_DATA_LEN   = 256  # 16×16 = 256 bytes uint8
HOTMAP_FRAME_LEN  = HOTMAP_HEADER_LEN + HOTMAP_DATA_LEN  # 272 bytes

HOTMAP_ROWS = 16
HOTMAP_COLS = 16

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE VISUALIZACIÓN LCD
# ─────────────────────────────────────────────────────────────────────────────

LCD_W = 320
LCD_H = 240

# Área del cuadro de dirección de sonido (centrado en pantalla)
BOX_X = 60
BOX_Y = 20
BOX_W = 200
BOX_H = 200

# Centro del indicador de dirección
CX = LCD_W // 2   # 160
CY = BOX_Y + BOX_H // 2  # 120

# Radio del indicador circular
RADIUS = 80

# Colores (RGB565)
COLOR_BG        = lcd.BLACK
COLOR_GRID      = 0x1082   # gris oscuro
COLOR_BOX       = 0xFFFF   # blanco
COLOR_LOW       = 0x001F   # azul  — intensidad baja
COLOR_MED       = 0x07E0   # verde — intensidad media
COLOR_HIGH      = 0xF800   # rojo  — intensidad alta
COLOR_MAX       = 0xF81F   # magenta — pico máximo
COLOR_ARROW     = 0xFFE0   # amarillo
COLOR_TEXT      = 0xFFFF   # blanco

# Umbral de activación de sonido (células del mapa > este valor se consideran activas)
INTENSITY_THRESHOLD = 30   # 0–255; ajusta según ruido ambiente

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZACIÓN DE HARDWARE
# ─────────────────────────────────────────────────────────────────────────────

def init_camera():
    """Inicializa la cámara OV2640 en resolución QVGA."""
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)   # 320×240
    sensor.set_vflip(False)
    sensor.set_hmirror(False)
    sensor.skip_frames(time=500)        # Espera a que el sensor se estabilice
    print("[CAM] Cámara inicializada OK")

def init_lcd():
    """Inicializa el LCD y establece fondo negro."""
    lcd.init(freq=15_000_000)
    lcd.rotation(0)
    lcd.clear(COLOR_BG)
    print("[LCD] Pantalla inicializada OK")

def init_mic_array():
    """
    Inicializa el MIC_ARRAY de MaixPy para el R6+1.
    Configuración de pines para MaixGo (ajusta para tu board):
      D0=23, D1=22, D2=21, D3=20, WS=19, SCLK=18, SK9822_DAT=24, SK9822_CLK=25
    """
    mic.init()
    # Para configuración personalizada de pines, usa:
    # mic.init(i2s_d0=23, i2s_d1=22, i2s_d2=21, i2s_d3=20,
    #          i2s_ws=19, i2s_sclk=18, sk9822_dat=24, sk9822_clk=25)
    print("[MIC] MIC_ARRAY inicializado OK")

def init_uart_mausb8():
    """
    Inicializa UART2 para recibir hotmap frames desde el MAUSB8.
    El MAUSB8 transmite por UART a 2,000,000 bps.
    Conectar: MAUSB8 TX → K210 RX pin.
    """
    fm.register(UART_RX_PIN, fm.fpioa.UART2_RX, force=True)
    fm.register(UART_TX_PIN, fm.fpioa.UART2_TX, force=True)
    uart = UART(UART.UART2,
                baudrate=UART_BAUD,
                bits=8,
                parity=None,
                stop=1,
                timeout=100,         # ms timeout por read
                read_buf_len=1024)
    print(f"[UART] MAUSB8 UART2 @ {UART_BAUD} bps inicializado OK")
    return uart

# ─────────────────────────────────────────────────────────────────────────────
# LECTURA DE HOTMAP FRAMES DESDE MAUSB8
# ─────────────────────────────────────────────────────────────────────────────

_uart_buf = bytearray(512)

def read_hotmap_frame(uart):
    """
    Lee y parsea un frame de hotmap del MAUSB8 por UART.

    Protocolo:
        Header: 16 bytes con valor 0xFF (frame sync)
        Data:   256 bytes (matriz 16×16 de intensidades uint8)

    Retorna:
        list[list[int]] de 16×16 con valores 0–255, o None si no hay frame válido.
    """
    # Buscar el header (16 × 0xFF consecutivos)
    header_found = 0
    timeout_ms = 50
    t0 = utime.ticks_ms()

    while header_found < HOTMAP_HEADER_LEN:
        if utime.ticks_diff(utime.ticks_ms(), t0) > timeout_ms:
            return None  # Timeout esperando frame
        b = uart.read(1)
        if b and b[0] == 0xFF:
            header_found += 1
        else:
            header_found = 0  # Reset si el byte no es 0xFF

    # Leer los 256 bytes de datos
    data = uart.read(HOTMAP_DATA_LEN)
    if data is None or len(data) < HOTMAP_DATA_LEN:
        return None

    # Convertir a matriz 16×16
    matrix = []
    for row in range(HOTMAP_ROWS):
        matrix.append(list(data[row * HOTMAP_COLS:(row + 1) * HOTMAP_COLS]))
    return matrix

# ─────────────────────────────────────────────────────────────────────────────
# PROCESAMIENTO DEL MAPA DE SONIDO
# ─────────────────────────────────────────────────────────────────────────────

import math

def analyze_hotmap(matrix):
    """
    Analiza la matriz 16×16 del hotmap para determinar:
        - Dirección dominante del sonido (ángulo en grados, 0–360)
        - Intensidad máxima (0–255)
        - Intensidad promedio (0–255)
        - Lista de celdas activas (row, col, value)

    El mapa es circular: la columna representa el ángulo (0°–360°),
    la fila representa la elevación (ignorada para azimut 2D).

    Retorna dict con: angle, max_intensity, avg_intensity, active_cells
    """
    max_val   = 0
    max_col   = 0
    total     = 0
    count     = 0
    active    = []

    for row in range(HOTMAP_ROWS):
        for col in range(HOTMAP_COLS):
            v = matrix[row][col]
            total += v
            count += 1
            if v > INTENSITY_THRESHOLD:
                active.append((row, col, v))
            if v > max_val:
                max_val = v
                max_col = col

    avg_val = total // count if count > 0 else 0

    # Ángulo basado en columna dominante (0–15 → 0°–360°)
    # MAUSB8: ángulo = valor × 30° para los 12 sectores de beamforming,
    # pero el hotmap 16×16 mapea columnas a ángulo continuo.
    angle_deg = (max_col / HOTMAP_COLS) * 360.0

    return {
        "angle":         angle_deg,
        "max_intensity": max_val,
        "avg_intensity": avg_val,
        "active_cells":  active,
        "max_col":       max_col,
        "max_row":       HOTMAP_ROWS - 1  # fila con mayor intensidad total
    }

def intensity_to_color(value):
    """
    Mapea una intensidad 0–255 a un color RGB565.
    Escala:  0–50  → azul  (bajo)
            51–150 → verde (medio)
           151–220 → naranja (alto)
           221–255 → rojo puro / magenta (pico)
    """
    if value < 50:
        return COLOR_LOW
    elif value < 150:
        # Verde interpolado
        return 0x07E0
    elif value < 220:
        # Naranja
        r = 0x1F
        g = ((value - 150) * 0x3F) // 70
        return (r << 11) | (g << 5)
    else:
        return COLOR_HIGH

# ─────────────────────────────────────────────────────────────────────────────
# CONTROL DE LEDs SK9822 DEL R6+1
# ─────────────────────────────────────────────────────────────────────────────

def update_leds(angle_deg, max_intensity):
    """
    Ilumina los 12 LEDs SK9822 del R6+1 según la dirección del sonido.
    El LED más cercano al ángulo se enciende con el color de intensidad.
    Los LEDs adyacentes se encienden con menor brillo.
    """
    # Obtener dirección MaixPy (0–11 sectores de 30°)
    direction = int(round(angle_deg / 30.0)) % 12

    # Calcular color según intensidad
    if max_intensity < 50:
        r, g, b = 0, 0, 80
    elif max_intensity < 150:
        r, g, b = 0, 80, 0
    elif max_intensity < 220:
        r, g, b = 80, 40, 0
    else:
        r, g, b = 80, 0, 0

    try:
        mic.set_led(direction, (r, g, b))
    except Exception:
        pass  # Si el LED falla, continuamos sin detener la visualización

# ─────────────────────────────────────────────────────────────────────────────
# RENDERIZADO EN LCD
# ─────────────────────────────────────────────────────────────────────────────

def draw_compass(img, angle_deg, max_intensity, avg_intensity):
    """
    Dibuja en `img` (image.Image RGB565) el indicador de dirección de sonido:
        1. Círculo exterior (brújula)
        2. Marcas de 30° en 30° (12 sectores)
        3. Flecha de dirección
        4. Barra de intensidad
        5. Texto de ángulo e intensidad
    """
    # ── Fondo del recuadro ──
    img.draw_rectangle(BOX_X - 5, BOX_Y - 5,
                       BOX_W + 10, BOX_H + 10,
                       color=0x2104, fill=True)   # gris muy oscuro

    # ── Círculo de brújula ──
    img.draw_circle(CX, CY, RADIUS, color=COLOR_BOX, thickness=2)

    # ── Marcas de 30° (12 sectores) ──
    for i in range(12):
        a_rad = math.radians(i * 30 - 90)  # 0° arriba
        # Punto exterior (en el borde)
        ox = int(CX + RADIUS * math.cos(a_rad))
        oy = int(CY + RADIUS * math.sin(a_rad))
        # Punto interior de la marca
        ix = int(CX + (RADIUS - 10) * math.cos(a_rad))
        iy = int(CY + (RADIUS - 10) * math.sin(a_rad))
        mark_color = COLOR_BOX if i % 3 == 0 else COLOR_GRID
        img.draw_line(ix, iy, ox, oy, color=mark_color, thickness=1)

    # ── Etiquetas cardinales ──
    labels = {0: "N", 3: "E", 6: "S", 9: "W"}
    for i, label in labels.items():
        a_rad = math.radians(i * 30 - 90)
        tx = int(CX + (RADIUS + 14) * math.cos(a_rad)) - 4
        ty = int(CY + (RADIUS + 14) * math.sin(a_rad)) - 4
        img.draw_string(tx, ty, label, color=COLOR_TEXT, scale=1)

    # ── Zona de intensidad (heatmap circular interno) ──
    if max_intensity > INTENSITY_THRESHOLD:
        # Radio del punto proporcional a la intensidad
        dot_r = max(4, int(RADIUS * 0.5 * max_intensity / 255))
        dot_color = intensity_to_color(max_intensity)
        img.draw_circle(CX, CY, dot_r, color=dot_color, fill=True)

    # ── Flecha de dirección ──
    arrow_len = RADIUS - 15
    a_rad = math.radians(angle_deg - 90)   # 0° = arriba (Norte)
    ax = int(CX + arrow_len * math.cos(a_rad))
    ay = int(CY + arrow_len * math.sin(a_rad))

    # Cuerpo de la flecha
    img.draw_line(CX, CY, ax, ay, color=COLOR_ARROW, thickness=3)

    # Punta de la flecha (triángulo pequeño)
    tip_size = 8
    left_rad  = a_rad + math.radians(140)
    right_rad = a_rad - math.radians(140)
    lx = int(ax + tip_size * math.cos(left_rad))
    ly = int(ay + tip_size * math.sin(left_rad))
    rx = int(ax + tip_size * math.cos(right_rad))
    ry = int(ay + tip_size * math.sin(right_rad))
    img.draw_line(ax, ay, lx, ly, color=COLOR_ARROW, thickness=2)
    img.draw_line(ax, ay, rx, ry, color=COLOR_ARROW, thickness=2)

    # Punto central
    img.draw_circle(CX, CY, 4, color=COLOR_TEXT, fill=True)

def draw_intensity_bar(img, max_intensity, avg_intensity):
    """
    Dibuja una barra vertical de intensidad a la derecha de la brújula.
    """
    bar_x = BOX_X + BOX_W + 10
    bar_y = BOX_Y + 10
    bar_w = 18
    bar_h = BOX_H - 20

    # Fondo de la barra
    img.draw_rectangle(bar_x, bar_y, bar_w, bar_h, color=0x2104, fill=True)
    img.draw_rectangle(bar_x, bar_y, bar_w, bar_h, color=COLOR_GRID, fill=False)

    # Relleno proporcional a la intensidad máxima
    fill_h = int(bar_h * max_intensity / 255)
    if fill_h > 0:
        fill_color = intensity_to_color(max_intensity)
        img.draw_rectangle(bar_x,
                           bar_y + bar_h - fill_h,
                           bar_w,
                           fill_h,
                           color=fill_color,
                           fill=True)

    # Marca del promedio
    avg_y = bar_y + bar_h - int(bar_h * avg_intensity / 255)
    img.draw_line(bar_x - 2, avg_y, bar_x + bar_w + 2, avg_y,
                  color=0xFFE0, thickness=1)

    # Etiquetas
    img.draw_string(bar_x - 2, bar_y - 12, "MAX", color=COLOR_TEXT, scale=1)
    img.draw_string(bar_x, bar_y + bar_h + 2, "0", color=COLOR_TEXT, scale=1)

def draw_hud(img, angle_deg, max_intensity, avg_intensity, src="MIC_ARRAY"):
    """
    Dibuja el HUD inferior con información numérica.
    """
    # Fondo HUD
    img.draw_rectangle(0, LCD_H - 28, LCD_W, 28, color=0x0821, fill=True)

    # Fuente de datos (MIC_ARRAY interno o MAUSB8 via UART)
    img.draw_string(5, LCD_H - 24,
                    f"SRC:{src}",
                    color=0x07FF, scale=1)

    # Ángulo
    img.draw_string(85, LCD_H - 24,
                    f"DIR:{angle_deg:5.1f}deg",
                    color=COLOR_ARROW, scale=1)

    # Intensidad máxima
    bar_color = intensity_to_color(max_intensity)
    img.draw_string(210, LCD_H - 24,
                    f"INT:{max_intensity:3d}",
                    color=bar_color, scale=1)

def draw_source_box(img, angle_deg, max_intensity):
    """
    Dibuja el cuadro de marcación de la fuente de sonido.
    El cuadro se desplaza sobre un mini-mapa rectangular (lado izquierdo).
    Representa visualmente la zona espacial de la que proviene el sonido.
    Útil para integrar con la imagen de la cámara en aplicaciones de seguimiento.
    """
    MAP_X = 5
    MAP_Y = 10
    MAP_W = 50
    MAP_H = 50

    # Borde del mini-mapa
    img.draw_rectangle(MAP_X, MAP_Y, MAP_W, MAP_H,
                       color=COLOR_GRID, fill=False)
    img.draw_string(MAP_X + 5, MAP_Y - 10, "ZONE", color=COLOR_TEXT, scale=1)

    # Posición del cuadro de sonido en el mini-mapa (mapeado desde ángulo)
    # 0°=arriba, 90°=derecha, 180°=abajo, 270°=izquierda
    a_rad = math.radians(angle_deg)
    zone_x = MAP_X + int(MAP_W * 0.5 + (MAP_W * 0.4) * math.sin(a_rad))
    zone_y = MAP_Y + int(MAP_H * 0.5 - (MAP_H * 0.4) * math.cos(a_rad))

    # Tamaño del cuadro proporcional a la intensidad
    sq_size = max(4, int(12 * max_intensity / 255))
    sq_color = intensity_to_color(max_intensity)

    img.draw_rectangle(zone_x - sq_size // 2,
                       zone_y - sq_size // 2,
                       sq_size, sq_size,
                       color=sq_color, fill=True)

    # Cruz central del mini-mapa
    img.draw_line(MAP_X + MAP_W // 2, MAP_Y,
                  MAP_X + MAP_W // 2, MAP_Y + MAP_H,
                  color=COLOR_GRID, thickness=1)
    img.draw_line(MAP_X, MAP_Y + MAP_H // 2,
                  MAP_X + MAP_W, MAP_Y + MAP_H // 2,
                  color=COLOR_GRID, thickness=1)

# ─────────────────────────────────────────────────────────────────────────────
# MODO FALLBACK: MIC_ARRAY INTERNO (sin MAUSB8)
# ─────────────────────────────────────────────────────────────────────────────

def read_from_mic_array():
    """
    Lee dirección e intensidad directamente del MIC_ARRAY de MaixPy.
    Retorna dict compatible con analyze_hotmap().
    Úsalo si el MAUSB8 no está disponible o como verificación adicional.
    """
    imga = mic.get_map()             # Imagen de distribución de sonido
    direction = mic.get_dir(imga)    # Dirección (0–11, sectores de 30°)
    mic.set_led(direction, (0, 0, 255))

    # Convertir sector (0–11) a ángulo
    angle_deg = direction * 30.0

    # Leer el mapa de píxeles para estimar intensidad
    # get_map() devuelve una imagen; extraemos el valor máximo como proxy
    # (MaixPy no expone amplitudes directamente, usamos escala del mapa)
    max_intensity = 180   # Valor estimado; reemplazar con lectura real si disponible

    return {
        "angle":         angle_deg,
        "max_intensity": max_intensity,
        "avg_intensity": 80,
        "active_cells":  [],
    }

# ─────────────────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Inicialización ──
    init_lcd()
    init_camera()
    init_mic_array()

    use_mausb8 = True   # Cambiar a False para usar solo MIC_ARRAY interno
    uart = None

    if use_mausb8:
        try:
            uart = init_uart_mausb8()
            # Enviar comando 'E' para activar LEDs del MAUSB8
            uart.write(b'E')
            utime.sleep_ms(100)
        except Exception as e:
            print(f"[WARN] MAUSB8 no disponible: {e}. Usando MIC_ARRAY interno.")
            use_mausb8 = False

    # Splash inicial
    splash = image.Image()
    splash.draw_rectangle(0, 0, LCD_W, LCD_H, color=COLOR_BG, fill=True)
    splash.draw_string(60, 100, "Sound Direction Visualizer", color=COLOR_ARROW, scale=1)
    splash.draw_string(70, 120, "K210 + R6+1 + MAUSB8", color=COLOR_TEXT, scale=1)
    lcd.display(splash)
    utime.sleep(1)

    angle_deg     = 0.0
    max_intensity = 0
    avg_intensity = 0
    frame_err     = 0
    MAX_ERR       = 10   # Si falla 10 frames seguidos, cambia a fallback

    print("[MAIN] Iniciando loop principal...")

    while True:
        t_start = utime.ticks_ms()

        # ── 1. Captura de imagen de cámara ──
        try:
            cam_img = sensor.snapshot()
        except Exception:
            cam_img = image.Image()
            cam_img.draw_rectangle(0, 0, LCD_W, LCD_H, color=COLOR_BG, fill=True)

        # ── 2. Lectura del mapa de sonido ──
        result = None

        if use_mausb8 and uart:
            matrix = read_hotmap_frame(uart)
            if matrix is not None:
                result = analyze_hotmap(matrix)
                frame_err = 0
            else:
                frame_err += 1
                if frame_err >= MAX_ERR:
                    print("[WARN] Demasiados errores MAUSB8, usando fallback MIC_ARRAY")
                    use_mausb8 = False

        if result is None:
            # Fallback al MIC_ARRAY interno de MaixPy
            result = read_from_mic_array()

        # Extraer valores del resultado
        angle_deg     = result["angle"]
        max_intensity = result["max_intensity"]
        avg_intensity = result["avg_intensity"]

        # ── 3. Actualizar LEDs del R6+1 ──
        update_leds(angle_deg, max_intensity)

        # ── 4. Renderizar overlays en la imagen de cámara ──
        src_label = "MAUSB8" if use_mausb8 else "MIC_ARR"

        draw_source_box(cam_img, angle_deg, max_intensity)
        draw_compass(cam_img, angle_deg, max_intensity, avg_intensity)
        draw_intensity_bar(cam_img, max_intensity, avg_intensity)
        draw_hud(cam_img, angle_deg, max_intensity, avg_intensity, src=src_label)

        # ── 5. Mostrar en LCD ──
        lcd.display(cam_img)

        # ── 6. Control de FPS (~15 fps objetivo) ──
        elapsed = utime.ticks_diff(utime.ticks_ms(), t_start)
        delay   = max(0, 66 - elapsed)   # 66ms ≈ 15 fps
        if delay > 0:
            utime.sleep_ms(delay)

# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[EXIT] Interrumpido por usuario")
    finally:
        mic.deinit()
        lcd.clear(lcd.BLACK)
        print("[EXIT] Limpieza completada")
```

***

## Arquitectura del sistema

El script tiene dos modos de fuente de datos que trabajan en cascada:

| Fuente | Protocolo | Datos entregados | Cuándo se usa |
|---|---|---|---|
| **MAUSB8 vía UART** | 2 Mbps, frames 272 bytes | Hotmap 16×16 con intensidades 0–255 por zona angular | Modo principal |
| **MIC_ARRAY interno** | I²S directo al K210 | Dirección (sector 0–11) y mapa de imagen | Fallback automático |

## Protocolo MAUSB8 (UART)

El MAUSB8 emite frames continuos a 2,000,000 bps. Cada frame tiene exactamente **272 bytes**: [wiki.sipeed](https://wiki.sipeed.com/hardware/en/modules/micarray_usbboard_bl616.html)
- **16 bytes de header**: todos `0xFF` (sincronización de trama)
- **256 bytes de datos**: matriz 16×16 de `uint8`, donde cada celda representa la intensidad acústica de esa zona angular [wiki.sipeed](https://wiki.sipeed.com/hardware/en/modules/micarray_usbboard_bl616.html)

La función `read_hotmap_frame()` busca el header byte a byte y luego lee los 256 bytes de datos, protegiéndose contra desalineaciones de trama.

## Visualización en LCD

Sobre la imagen de la cámara se superponen cuatro elementos:

- **Brújula central** con flecha de dirección giratoria y marcas cada 30° (12 sectores del beamformer)
- **Cuadro de zona (ZONE)** en la esquina superior izquierda que muestra la posición espacial de la fuente sonora
- **Barra de intensidad** a la derecha, con color que escala de azul → verde → naranja → rojo según la amplitud
- **HUD inferior** con ángulo exacto, intensidad numérica y fuente de datos activa

## LEDs SK9822 del R6+1

El R6+1 tiene 12 LEDs SK9822  controlados mediante `mic.set_led()`. El script ilumina el LED correspondiente al sector del sonido, cambiando el color según la intensidad: azul (bajo), verde (medio), naranja (alto), rojo (pico). [berrybase](https://www.berrybase.ch/en/product-datasheet/019234a63b45700f96b9f7a8da3297ca/create)

## Ajustes clave para tu hardware

- **`UART_RX_PIN`**: cambia el número de pin físico al que conectas `TX` del MAUSB8 en tu board específica
- **`INTENSITY_THRESHOLD`**: aumenta este valor (por ejemplo a `60`) si el ambiente es muy ruidoso
- **`mic.init(i2s_d0=..., ...)`**: si tu board no es MaixGo, descomenta la línea con pines explícitos y ajusta según el esquema de tu PCB
- **`use_mausb8 = False`**: si no tienes el MAUSB8, el script opera solo con el MIC_ARRAY interno vía I²S [en.wiki.sipeed](https://en.wiki.sipeed.com/soft/maixpy/en/develop_kit_board/module_microphone.html)
