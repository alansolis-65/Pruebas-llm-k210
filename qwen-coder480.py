import sensor
import image
import lcd
import KPU as kpu
import time

# Inicializar la cámara
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

# Inicializar la pantalla LCD
lcd.init()

# Cargar el modelo KPU para detección de rostros
task = kpu.load("/sd/face_detection.kmodel")  # Asegúrate de que el modelo esté en la SD

# Configurar la entrada del modelo
anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.35742, 5.155437, 6.92275, 6.718375, 9.01025)  # Ajusta según tu modelo
kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

# Variables para almacenar la posición anterior del rostro
prev_x, prev_y, prev_w, prev_h = 0, 0, 0, 0

while True:
    # Capturar una imagen
    img = sensor.snapshot()
    
    # Ejecutar la detección de rostros
    code = kpu.run_yolo2(task, img)
    
    if code:
        for i in code:
            # Obtener las coordenadas del rostro detectado
            x, y, w, h = i.x(), i.y(), i.w(), i.h()
            
            # Dibujar un recuadro verde alrededor del rostro
            img.draw_rectangle(x, y, w, h, color=(0, 255, 0), thickness=2)
            
            # Comparar con la posición anterior
            if prev_w != 0 and prev_h != 0:
                # Calcular el centro del rostro actual y anterior
                center_x = x + w // 2
                center_y = y + h // 2
                prev_center_x = prev_x + prev_w // 2
                prev_center_y = prev_y + prev_h // 2
                
                # Determinar el movimiento
                if w * h > prev_w * prev_h:
                    movement = "Se ha acercado"
                elif w * h < prev_w * prev_h:
                    movement = "Se ha alejado"
                elif center_x > prev_center_x + 10:
                    movement = "Movido a la derecha"
                elif center_x < prev_center_x - 10:
                    movement = "Movido a la izquierda"
                else:
                    movement = "Sin movimiento significativo"
                
                # Mostrar el movimiento en la imagen
                img.draw_string(10, 10, movement, color=(255, 255, 255), scale=2)
            
            # Actualizar la posición anterior
            prev_x, prev_y, prev_w, prev_h = x, y, w, h
    
    # Mostrar la imagen en la pantalla LCD
    lcd.display(img)

# Liberar recursos (opcional, si se sale del bucle)
kpu.deinit(task)
