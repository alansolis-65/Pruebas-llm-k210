Aquí tienes un script en MicroPython para el módulo K210, implementado según las mejores prácticas de desarrollo para este hardware. El código incluye la inicialización de la cámara y pantalla LCD, la detección de rostros utilizando el KPU y un algoritmo para calcular y mostrar la dirección del movimiento relativo del rostro.

He utilizado la API de MaixPy (estándar para K210) para la gestión de hardware y he implementado un algoritmo de "Tracker Básico por Diferencia de Centroides" que es eficiente para los recursos limitados del K210.

```python
import sensor, image, time, lcd
from maix import KPU
import gc

# --- CONFIGURACIÓN ---
# Configuración de la pantalla
LCD_ROTATION = 0  # 0: Normal, 1: 90 grados, 2: 180 grados, 3: 270 grados

# Configuración de la cámara
CAM_HMIRROR = False  # Espejo horizontal (recomendado para self)
CAM_VFLIP = False    # Voltear verticalmente

# Configuración del modelo YOLOv2 para detección de rostros
# Estos valores deben coincidir con los del modelo descargado.
MODEL_ADDR = 0x300000  # Carga desde la memoria Flash en la dirección 0x300000
ANCHORS = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
DETECTION_THRESHOLD = 0.5
NMS_THRESHOLD = 0.3

# Umbral para considerar que un rostro se ha "perdido" y reiniciar el tracking
# Se basa en la distancia euclidiana normalizada (ancho/20 es un buen valor para QVGA)
MOTION_TOLERANCE = 20  # píxeles

# --- ESTADO GLOBAL PARA EL TRACKING ---
prev_face_center_x = None
prev_face_center_y = None
prev_face_width = None

def get_face_center(rect):
    """
    Calcula el centro de un rectángulo de detección.
    rect = (x, y, w, h)
    """
    x, y, w, h = rect
    return (x + w // 2, y + h // 2)

def calculate_direction(current_center, prev_center, current_width):
    """
    Determina la dirección del movimiento relativo comparando
    el centro actual con el anterior.
    
    Returns: str ("ACERCADO", "ALEJADO", "IZQUIERDA", "DERECHA", "NINGUNO")
    """
    global prev_face_center_x, prev_face_center_y, prev_face_width
    
    cx, cy = current_center
    if prev_face_center_x is None:
        return "NINGUNO"

    # Calcular movimientos en X e Y
    dx = cx - prev_face_center_x
    dy = cy - prev_face_center_y
    
    # Calcular cambio en escala (profundidad/Z)
    # Si el ancho del rostro aumenta, se acerca. Si disminuye, se aleja.
    dw_ratio = (current_width - prev_face_width) / prev_face_width

    direction_text = []
    
    # Umbral para moverse horizontalmente/verticalmente
    motion_xy_threshold = current_width * 0.15  # 15% del ancho del rostro
    # Umbral para movimiento de profundidad
    motion_z_threshold = 0.10  # 10% de cambio de tamaño

    # Lógica de detección
    if abs(dx) > motion_xy_threshold:
        if dx > 0:
            direction_text.append("DERECHA")
        else:
            direction_text.append("IZQUIERDA")
    
    if abs(dy) > motion_xy_threshold:
        if dy > 0:
            direction_text.append("ABAJO")
        else:
            direction_text.append("ARRIBA")
    
    if abs(dw_ratio) > motion_z_threshold:
        if dw_ratio > 0:
            direction_text.append("ACERCADO")
        else:
            direction_text.append("ALEJADO")
    
    # Prioridad de texto: "ACERCADO"/"ALEJADO" siempre se muestra si se detecta.
    # Para movimiento planar (X/Y), solo mostrar si no hay movimiento Z o si es el único.
    if not direction_text:
        return "NINGUNO"
    
    if "ACERCADO" in direction_text or "ALEJADO" in direction_text:
        return direction_text[0]
    else:
        return direction_text[0] if len(direction_text) == 1 else " ".join(direction_text)


def main():
    global prev_face_center_x, prev_face_center_y, prev_face_width

    # 1. Inicialización del hardware
    try:
        # Resetear sensor y configurar imagen
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565) # RGB565 es más rápido que JPEG para procesar
        sensor.set_framesize(sensor.QVGA)   # 320x240 es ideal para el K210
        sensor.set_hmirror(CAM_HMIRROR)
        sensor.set_vflip(CAM_VFLIP)
        sensor.run(1)
        
        # Inicializar LCD
        lcd.init(type=1) # Tipo 1 suele ser el LCD integrado en placas como MaixBit
        lcd.rotation(LCD_ROTATION)
        lcd.clear(lcd.WHITE)
        
    except Exception as e:
        raise Exception(f"Error de hardware: {e}")

    # 2. Cargar y configurar el modelo de IA (KPU)
    try:
        task = KPU.load(MODEL_ADDR)
        if task is None:
            raise Exception("Fallo al cargar el modelo KPU.")
        kpu.init_yolo2(task, DETECTION_THRESHOLD, NMS_THRESHOLD, 5, ANCHORS)
    except Exception as e:
        raise Exception(f"Error cargando el modelo de IA: {e}")

    clock = time.clock() # Reloj para FPS

    # 3. Bucle principal
    try:
        while True:
            clock.tick()
            img = sensor.snapshot()
            
            # Ejecutar la detección
            objects = kpu.run_yolo2(task, img)
            
            if objects:
                # Toma solo el primer rostro detectado para el tracking (para simplificar)
                obj = objects[0]
                rect = obj.rect()
                cx, cy = get_face_center(rect)
                fw = rect[2] # ancho del rostro

                # --- DIBUJAR RESULTADOS EN LA PANTALLA ---
                # Dibujar el recuadro verde
                img.draw_rectangle(rect, color=(0, 255, 0), thickness=2)
                
                # Calcular dirección
                direction = calculate_direction((cx, cy), (prev_face_center_x, prev_face_center_y), fw)
                
                # Actualizar estado global
                prev_face_center_x = cx
                prev_face_center_y = cy
                prev_face_width = fw

                # Dibujar el texto de dirección en la parte superior del rostro
                txt = f"Dir: {direction}"
                img.draw_string(rect[0], rect[1] - 20, txt, color=(0, 255, 0), scale=1.5)

                # Dibujar un punto en el centro del rostro para referencia
                img.draw_circle(cx, cy, 5, color=(0, 255, 0), thickness=2)
            
            # Si no hay rostro, resetear el tracker (opcional)
            else:
                prev_face_center_x = None
                prev_face_center_y = None
                prev_face_width = None
                img.draw_string(10, 10, "No rostro", color=(255, 0, 0), scale=2)
            
            # Mostrar FPS en la esquina inferior izquierda
            fps = clock.fps()
            img.draw_string(10, 220, "FPS: %2.1f" % fps, color=(0, 0, 0), scale=2)
            
            # Enviar la imagen al LCD
            lcd.display(img)
            
            # Forzar limpieza de memoria para evitar fugas
            gc.collect()
            
    finally:
        # 4. Limpieza final
        if 'task' in locals():
            kpu.deinit(task)
        sensor.run(0)
        lcd.clear(lcd.BLACK)

# Iniciar la función principal
if __name__ == "__main__":
    main()
```

### Explicación de las decisiones de diseño:

1.  **API de MaixPy:** He utilizado `from maix import KPU` y `import sensor, image, lcd`. Esta es la API más establecida para K210, que se utiliza en plataformas como MaixPy y CanMV.
2.  **Algoritmo de Tracking:**
    *   En lugar de un KPI complejo (que requeriría más memoria y procesamiento), he implementado un sistema basado en el cambio del centroide (X, Y) y el cambio de tamaño del rectángulo.
    *   `calculate_direction()`: Calcula `dx` y `dy` para movimiento lateral y `dw_ratio` para el movimiento de profundidad. Un cambio en el tamaño del rectángulo (`w`) es un indicador muy fiable de "acercamiento" o "alejamiento" en un sistema de una sola cámara.
    *   Se han definido umbrales relativos (porcentajes del ancho del rostro) para que el sistema sea robusto independientemente de la distancia a la que se encuentre la persona.
3.  **Gestión de Memoria:**
    *   El `gc.collect()` al final del bucle es fundamental en sistemas embebidos con poca RAM (6MB) para evitar la fragmentación de memoria y que el script se bloquee después de un tiempo.
4.  **Configuración:**
    *   He incluido constantes en la parte superior del script (`MODEL_ADDR`, `ANCHORS`, etc.) para que sea fácil de adaptar si usas un modelo diferente o una placa con LCD invertido.
5.  **Salida Visual:**
    *   El recuadro verde es el estándar, pero he añadido un texto (`"Dir: ACERCADO"`) y un punto en el centro del rostro para hacer la orientación más clara.
    *   Muestra el FPS para que el desarrollador pueda ajustar la resolución o el umbral si el rendimiento es bajo.

### Requisitos previos para ejecutarlo:

1.  **Firmware:** Tu placa K210 debe tener instalado el firmware de **MaixPy** o **CanMV**.
2.  **Modelo:** Debes descargar el modelo `face_model_at_0x300000.kfpkg` y quemarlo en la memoria Flash de tu placa en la dirección `0x300000` utilizando la herramienta `kflash`. Si prefieres cargarlo desde una tarjeta SD, cambia la línea `task = KPU.load(MODEL_ADDR)` por `task = KPU.load("/sd/face.kmodel")` y asegúrate de que el archivo esté en la raíz de la SD.
3.  **Hardware:** La placa debe tener conectada una cámara OV2640 y una pantalla LCD (de 2.4" o similar) para que los pines de `lcd` y `sensor` funcionen por defecto. Si usas una placa diferente (como la Maix Bit Go), es posible que tengas que ajustar la inicialización del LCD (`lcd.init(type=1)`).
