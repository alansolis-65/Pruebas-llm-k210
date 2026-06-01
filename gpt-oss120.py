import sensor, image, time, lcd
from maix import KPU
import gc

# --- Configuración de la pantalla y la cámara ---
lcd.init()
lcd.rotation(0)  # Rotación de la pantalla (0, 1, 2, 3)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320x240
sensor.skip_frames(time=2000)
clock = time.clock()

# --- Configuración del modelo KPU (YOLOv2 para detección de rostros) ---
# Nota: Asegúrate de que el archivo de modelo 'face_detect.kmodel' esté en la raíz de tu SD o Flash.
# Un modelo popular es 'face_detect_320x240.kmodel' disponible en maixhub.com
kpu = KPU()
try:
    # Intenta cargar el modelo del dispositivo (ej. flash)
    # kpu.load(0x300000) # Comentar si no se usa este método
    # Usando el método de archivo .kmodel es más flexible para pruebas
    kpu.load_kmodel("/sd/face_detect.kmodel")
except Exception as e:
    print("Error loading model:", e)
    print("Please ensure 'face_detect.kmodel' is in the correct path.")
    print("Using a simpler template for demonstration if model fails.")
    # Para la demostración, si falla la carga, definimos una clase de KPU vacía
    class DummyKPU:
        def run_with_output(self, img):
            return None
        def deinit(self):
            pass
    kpu = DummyKPU()

# Parametrización de la detección (ajustar según el modelo)
# Estos valores son comunes para modelos de 320x240
anchor = (0.1075, 0.126875, 0.126875, 0.175, 0.1465625, 0.2246875, 0.1953125, 0.25375, 0.2440625, 0.351875, 0.341875, 0.4721875, 0.5078125, 0.6696875, 0.8984375, 1.099687, 2.129062, 2.425937)
kpu.init_yolo2(anchor, anchor_num=9, img_w=320, img_h=240, net_w=320, net_h=240, layer_w=10, layer_h=8, threshold=0.7, nms_value=0.3, classes=1)

# --- Variables para el seguimiento ---
# Estado del sistema: True = capturando referencia, False = siguiendo
capture_reference = True  
ref_center_x = None
ref_center_y = None
ref_w = None
ref_h = None

# Margen de tolerancia para los cálculos de movimiento (en píxeles)
# Un valor mayor hace que el sistema sea menos sensible.
MOVEMENT_THRESHOLD = 20 

print("Script ready.")
print("Please present a face to the camera to capture the reference position.")

# --- Bucle Principal ---
while True:
    clock.tick()
    img = sensor.snapshot()
    dect = None

    # 1. Ejecutar la detección de rostros
    if not isinstance(kpu, DummyKPU): # Si el modelo se cargó correctamente
        kpu.run_with_output(img)
        dect = kpu.regionlayer_yolo2()

    # 2. Procesar resultados de la detección
    if dect and len(dect) > 0:
        for l in dect:
            # l = [x, y, w, h]
            x, y, w, h = l[0], l[1], l[2], l[3]
            center_x = x + w // 2
            center_y = y + h // 2

            # Dibujar el recuadro verde (o el color de referencia)
            if capture_reference:
                # Mientras capturamos la referencia, usamos un color diferente (naranja)
                a = img.draw_rectangle(x, y, w, h, color=(0, 165, 255))
                # Si es la primera detección, capturamos la referencia
                if ref_center_x is None:
                    ref_center_x = center_x
                    ref_center_y = center_y
                    ref_w = w
                    ref_h = h
                    capture_reference = False # Ya ha capturado, ahora pasa a seguir
                    print("Reference captured! Tracking mode active.")
                    print(f"Ref Pos: X={ref_center_x}, Y={ref_center_y}, W={ref_w}, H={ref_h}")
            else:
                # En modo seguimiento, usamos el color verde estándar
                a = img.draw_rectangle(x, y, w, h, color=(0, 255, 0))
                
                # --- Lógica de Comparación de Posición ---
                label = None

                # Eje X (Izquierda/Derecha)
                if center_x > ref_center_x + MOVEMENT_THRESHOLD:
                    label = "DERECHA"
                elif center_x < ref_center_x - MOVEMENT_THRESHOLD:
                    label = "IZQUIERDA"
                else:
                    label = "X_ESTATICO"

                # Eje Y (Cerca/Alejado)
                # Como Y aumenta hacia abajo, si el rostro "sube" (y disminuye), se ha acercado.
                if center_y < ref_center_y - MOVEMENT_THRESHOLD:
                    label += " / ACERCANDO"
                elif center_y > ref_center_y + MOVEMENT_THRESHOLD:
                    label += " / ALEJANDO"
                elif label == "X_ESTATICO":
                    label = "ESTATICO"

                # Dibujar la etiqueta de texto en la pantalla
                a = img.draw_string(x + w + 5, y, label, scale=1.5, color=(0, 255, 0))
                
                # Opcional: Dibujar un punto para indicar el centro de referencia
                a = img.draw_circle(ref_center_x, ref_center_y, 3, color=(255, 0, 0), thickness=2)
                a = img.draw_circle(center_x, center_y, 3, color=(0, 255, 0), thickness=2)

    # 3. Mostrar la FPS y la imagen en el LCD
    fps = clock.fps()
    a = img.draw_string(2, 2, "%2.1ffps" % fps, scale=2.0, color=(255, 0, 0))
    lcd.display(img)
    
    # Pequeña pausa para no sobrecargar el sistema
    gc.collect()
    # time.sleep_ms(10) # No es estrictamente necesario si el sensor ya tiene un control de FPS interno

# --- Limpieza al salir (no reached en loop infinito) ---
if not isinstance(kpu, DummyKPU):
    kpu.deinit()
