Razonamiento Pro
Evaluando el uso adecuado de herramientas
Parece que me piden usar una herramienta de generación de imágenes, pero el sistema dice que no debo responder después de generar. Esto podría afectar la respuesta al usuario. El usuario también está buscando información de hardware actualizada sobre K210, MicroPython, y algunos accesorios específicos. Tal vez necesite buscar en línea y comprender mejor las API de MicroPython antes de generar un script adecuado.

Buscando información sobre MaixPy y hardware K210
Investigando protocolo y formato para MA-USB8
Parece que necesito entender el formato de datos del firmware MA-USB8, que usa UAC2.0 para audio y UART para comunicación. Sin embargo, el K210 no puede actuar como host USB, lo que limita el uso de UAC. Debo investigar cómo conectarlo mediante UART y entender su protocolo y formato de tramas.

Buscando formato de datos del firmware MA-USB8
Evaluando opciones para usar MAUSB8 y K210
Parece que necesito decidir cómo conectar el MAUSB8 al K210 usando UART, ya que no puedo usar UAC por la falta de soporte USB en el K210. El proceso podría implicar usar el micrófono directamente con el K210 o explorar el uso del KPU, aunque este último no parece necesario para la tarea.

Implementando el análisis de hotmap con MAUSB8
El MAUSB8 envía el mapa de calor a través de UART con 16x16 celdas y no provee audio por USB, lo cual limita el uso de canales individuales. Necesito mapear el hotmap a las coordenadas de la cámara y dibujar un rectángulo alrededor de la celda de mayor intensidad en la pantalla LCD para mostrar la dirección del sonido.

Verificando APIs de UART para K210
Necesito investigar cómo usar las APIs de UART en MaixPy. Usualmente, esto se hace importando UART desde machine y configurando los pines con fpioa_manager. Debería confirmar esto en la documentación para asegurarme de que todo esté configurado correctamente, y luego puedo avanzar con el código necesario.

Buscando documentación sobre APIs UART y MaixPy
Revisando documentación de UART y sensores
Creo que necesito abrir y revisar la documentación sobre UART y los sensores. Esto me ayudará a comprender cómo conectar todo correctamente y cómo integrar la funcionalidad de dibujo en el proyecto. Necesito asegurarme de tener claro cómo interactúan estos componentes.

Buscando documentación sobre UART y sensores
Revisando la API de MaixPy para draw_rectangle
Creo que debería inspeccionar la API de MaixPy, específicamente los parámetros para draw_rectangle. Podría ser útil buscar "draw_rectangle" directamente para encontrar la fuente adecuada. Esto me ayudará a comprender cómo manipular y dibujar la imagen correctamente para adaptarla a mis necesidades.

Buscando parámetros de la API draw_rectangle de MaixPy
Preparando script y verificando pinout de MAUSB8
Voy a desarrollar un "script principal para MAUSB8 via UART", y también un "script alternativo directos MIC_ARRAY" si el usuario no usa MAUSB8. Además, necesito verificar los pines de UART en MAUSB8. El manual menciona usar USB/USB2TTL para conexión, pero debo buscar la información de los pines.

Buscando información sobre MAUSB8 y pines UART
Creando código para procesar frames de MAUSB8
Estoy pensando en cómo crear un código robusto en MicroPython para procesar los frames del MAUSB8 a través de UART a 2M. Cada frame es de 272 bytes, y necesito asegurarme de que la sincronización se haga correctamente al buscar el encabezado. El uso de find o bytes.find podría ayudar, pero debo tener cuidado con la eficiencia al manejar esos datos.

Mejorando el código de procesamiento de frames
He simplificado el código para leer frames a través de UART. Lo que hago es buscar el encabezado de 16 bytes (HDR). Si el find se alinea al encontrar los 0xFF, debería estar bien, siempre y cuando no haya cabecera previa. Después de sincronizar y verificar la longitud, se obtiene el frame correcto.

Mejorando el procesamiento de frames y cálculo de zonas calientes
Puedo usar bytes.find en MicroPython. El enfoque que tengo es buscar el encabezado de 16 bytes, ajustar el búfer y devolver un payload de 256 bytes. Luego, en el algoritmo de procesamiento de zonas calientes, mapearé regiones con valores máximos y filtraré el ruido utilizando un umbral. Estoy considerando cómo usar un umbral para estabilizar las coordenadas.

Ajustando visualización de intensidad en código
MicroPython permite ajustar los rectángulos según la intensidad, utilizando diferentes colores. El código se organiza para cambiar los colores (verde, amarillo, rojo) dependiendo del valor de intensidad. Además, calculo el tamaño del rectángulo según la intensidad, y dibujo una cruz en la posición central con un tamaño proporcional, todo con parámetros ajustables.

Configuración de cámara y comunicación UART
Configuro el mapa y la inicialización del sensor, ajustando la resolución y la frecuencia. Al principio, no estoy seguro si debe inicializarse la pantalla o el sensor antes, pero ambos métodos funcionan. Necesito decidir qué pines del K210 usar; por ejemplo, IO10 y IO11 para UART, asegurándome de conectar adecuadamente GND y considerar el voltaje TTL.

Consideraciones sobre el tamaño del búfer y el procesamiento de frames
Estoy evaluando el tamaño del búfer para el UART. Si usamos 2Mbps, la tasa de datos es 250KB/s y un búfer de 16KB podría no ser suficiente. Entonces, ajusto el tamaño del búfer a 16384 y necesito que la cámara procese datos a 10-15 fps y que se manejen múltiples frames para evitar desbordes.

Definiendo la función hottest_cell y mapeo al gráfico
Estoy trabajando en la función hottest_cell para identificar el centro del área más intensa en el mapa. Si el valor máximo es bajo, la función retorna None. Si no, calcula el centro de masa de las celdas superiores al umbral. Luego, mapeo las coordenadas al área de la pantalla. Hay que mantener en cuenta que la fuente del sonido puede no estar alineada verticalmente.

Ajustando la orientación y calibración
Para visualizar la estimación de dirección en la cámara, debo calibrar parámetros como X_MIRROR, Y_MIRROR y ROI, así como la orientación del micrófono. También es útil añadir opciones de rotación y volteo configurables mediante sensor.set_hmirror o set_vflip. En cuanto al KPU, no es necesario para la superposición de UART/audio, solo para detección de objetos, por lo que puedo especificarlo claramente.

Aclarando el uso del micrófono y la salida hotmap
El script actual usa la salida de mapas de calor, no el audio UAC de 8 canales. Si se necesita leer la intensidad por micrófono, se necesita un host USB o un controlador I2S directo. Aunque no es obligatorio, podría incluirse el comando uart.write(b'E') para encender LEDs sin interferir con el flujo.

Envío de comandos para ajustar la salida
Para asegurar la salida en formato crudo, puedo enviar b'fcE', lo cual apaga la salida ASCII y pseudocolor, mientras enciende los LEDs. Aunque no es necesario, también se puede ajustar el umbral de activación del localizador con los comandos t o T. Además, proporcionaré el código main.py si es necesario.

Incluir conexión y citaciones
Para conectar el MAUSB8 al K210, se conecta el TX del MAUSB8 al IO11 del K210. El RX del MAUSB8 se conecta opcional

Decidiendo entre alternativas en el script
El usuario no solicitó imágenes, así que no las incluiré a menos que sea necesario. El código debe ser directo y eficiente. Incluiré la alternativa de utilizar MIC_ARRAY solo si es relevante para el caso del usuario (sin MAUSB8). El script de MicroPython debería ser suficiente, sin excesos.

Verificando la sintaxis sin necesidad de ejecución
No hace falta crear un archivo o compilar el código. Aunque podría validar la sintaxis usando Python o incluso con MicroPython, no es estrictamente necesario. El código debería estar bien, incluso con const, si se importa correctamente en MicroPython. No usaré herramientas adicionales, ya que no se requiere ejecución.

Verificando función `sensor.reset` y soporte de `dual_buff`
El código usa sensor.reset(freq=24000000, dual_buff=True), pero parece que no todos los firmwares admiten el soporte de dual_buff. La documentación menciona que este parámetro puede no estar disponible en versiones anteriores del firmware. Es importante asegurarse de que el dispositivo tenga soporte para dual_buff en la versión de maixpy utilizada.

Considerando posibles valores de timeout en UART y manejo de búfer
Parece que los parámetros de la comunicación UART incluyen bits de datos, bits de parada y paridad (8, 1, 0) según la documentación. Estoy proponiendo usar timeout=0 para evitar bloqueos si no se recibe datos, aunque MaixPy parece establecer el timeout=1000. Puede que sea mejor usar timeout=10 si el valor 0 no es compatible.

Manejando los búferes de recepción y el encabezado
Cuando se manipula el búfer rxbuf, la asignación rxbuf = rxbuf[-keep:] requiere la palabra clave global para modificarlo. El uso de un segmento de bytearray es correcto. Me preocupa que si el payload contiene solo 0xFF y se encuentra el encabezado rápidamente, podría interrumpir el análisis, pero al procesarlo de manera fija eso se evita.

Manejando ruido y suavizado en pantalla
Con el ruido ambiental alto, el pico necesita destacar, así que tengo que asegurarme de que las señales sean visibles. En cuanto a la función map_to_screen, la resolución de pantalla es importante, por lo que usaré constantes para IMG_W y IMG_H, pero podría considerar usar la función sensor.width() para mayor flexibilidad. Además, el suavizado de puntos con smooth_point es clave para mejorar la precisión visual sobre movimientos pequeños.

Manejo de visualización de picos en la pantalla
Estoy configurando el tamaño y el color para dibujar rectángulos y cruces en la pantalla, dependiendo del valor del "peak". El grosor del rectángulo varía según el valor de "peak", y también uso funciones de dibujo para mostrar las ubicaciones de los picos. Sin embargo, necesito confirmar los parámetros correctos para la función draw_cross.

Buscando información sobre parámetros de dibujo
Verificando detalles del código y optimizaciones
Estoy considerando cómo organizar el código, tal vez con comentarios más claros en lugar de citas. Es importante tener en cuenta si el código se ejecuta en MicroPython o MaixPy para su manejo del tiempo. También estoy planificando una optimización: ejecutar una recolección de basura cada 60 cuadros. El código principal maneja la detección de fuentes sonoras y la visualización de la imagen de la cámara.

Pensó durante 4m 59s
Listo

Fuentes
·
61

Sipeed Wiki
MicArray UAC Drive Board MA-USB8 — User Guide - Sipeed Wiki

Sipeed Wiki
machine.UART - Sipeed Wiki

Sipeed Wiki
sensor (camera) - Sipeed Wiki

Sipeed Wiki
lcd (screen display) - Sipeed Wiki

Sipeed Wiki
image (machine vision) - Sipeed Wiki

sipeed.com
MicArray UAC Drive Board MA-USB8 — User Guide - Sipeed Wiki
30 de noviembre de 2025 — MA-USB8 is a USB audio + serial interface drive board designed for MicArray microphone modules. It forwards the array’s audio (via UAC2.0, 8 channels) and sends soundfield hotmap frames (via CDC ACM o...
github.com
MicArray UAC Drive Board MA-USB8 — User Guide - GitHub
21 de agosto de 2025 — MA-USB8 is a USB audio + serial interface drive board designed for MicArray microphone modules. It forwards the array’s audio (via UAC2.0, 8 channels) and sends soundfield hotmap frames (via CDC ACM o...

maixhub.com
MaixPy中如何获取Sipeed 6+1Mic Array各MIC的PCM数据
25 de mayo de 2025 — 目前，MaxiPy 例程中，通过GCC-PHAT算法实现声源定位、语音识别、波束成形等，其输出只有imga = mic.get_map () ，获取声音源分布图像。 无法获取声音原始数据。 如果按下面这个方式配置好，获取的数据。 这个是获取了所有 7个MIC的数据，还是只获取了0，1，2 ，3 中某个通道的左右声道数据？ 这些数据在data中是怎么排列的? 如果我想取左声道的数据，对于data.t...

deepwiki.com
MaixPy & MaixPy3 | sipeed/sipeed_wiki | DeepWiki
19 de mayo de 2025 — MaixPy is based on MicroPython and designed specifically for the K210 chip. It offers a simplified Python environment for embedded development with built-in support for machine vision, AI model infere...

deepwiki.com
Getting Started | sipeed/MaixPy-v1 | DeepWiki
24 de abril de 2025 — This document provides instructions for setting up and beginning to use MaixPy, a MicroPython implementation designed for the Kendryte K210 AI chip. This guide covers obtaining the firmware, flashing...

deepwiki.com
Image Processing | sipeed/MaixPy-v1 | DeepWiki
24 de abril de 2025 — This document explains the image processing capabilities available in MaixPy, built on the OpenMV library and adapted for the K210 processor. It covers the core image representation, manipulation, and...

deepwiki.com
LCD Display | sipeed/MaixPy-v1 | DeepWiki
24 de abril de 2025 — This page documents the LCD display interface in MaixPy, which allows users to interact with and control LCD screens connected to Sipeed Maix boards. The LCD module provides functions for initializing...
github.com
sipeed_wiki/docs/soft/maixpy/en/api_reference/machine_vision/lcd.md at ...
17 de abril de 2025 — roi is a rectangular tuple (x, y, w, h) of a region of interest. If not specified, it is the image rectangle. If the roi width is smaller than the lcd width, use a vertical black border to center the...
github.com
sipeed_wiki/docs/soft/maixpy/en/api_reference/machine_vision/sensor.md ...
2 de marzo de 2025 — If you need to customize the sequence of setting the pixel format, you can set it to False, and then use the sensor.__write_reg(addr, value) function to customize the write register sequence. Availabl...

01studio.cc
Camera | 01Studio
7 de noviembre de 2024 — Click the serial terminal in the lower left corner, and you can see the current FPS (frames per second) value is about 30 frames in real time. Through this experiment, we understand the principles and...
github.com
sipeed_wiki/docs/soft/maixpy/en/api_reference/machine/uart.md at main ...
30 de septiembre de 2024 — There are 3 uarts in k210, and each uart can be freely mapped. Before using uart, we need to use fm to map and manage the chip pins. As shown below, set PIN10 as the sending pin of uart2 and PIN11 as...

circuitdigest.com
Maxduino for AI and ML: A Comprehensive Guide to Advanced Solutions
15 de septiembre de 2024 — First, we will learn how to flash the Micropython firmware to the Maixduino and then how to set up Sipeed’s Maixpy IDE and use AI and Machine Learning with the board.

sipeed.com
MicArray 麦克风阵列 - Sipeed Wiki
24 de julio de 2024 — Sipeed microphone array consists of six microphones along the board and a center microphone. The 12 leds on the array board can be used to visualize and identify the location of the sound source, whic...

sipeed.com
MaixCAM MaixPy Basic Image Operations - Sipeed
2 de abril de 2024 — By providing the coordinates of three or more points in the current image and the corresponding coordinates in the target image, you can automatically perform operations such as rotation, scaling, and...

howwhatproduce.com
Detección de objetos con placas Sipeed MaiX (Kendryte K210): 6 pasos
29 de enero de 2024 — Reconocimiento de imágenes con placas K210 y Arduino IDE / Micropython: ya escribí un artículo sobre cómo ejecutar demostraciones de OpenMV en Sipeed Maix Bit y también hice un video de demostración d...

csdn.net
使用MaixPy进行LCD显示与感光元件配置教程-CSDN博客
23 de enero de 2024 — 如果需要自定义设置像素格式的序列，可以设置为 False，然后使用 sensor.__write_reg(addr, value) 函数自定义写寄存器序列. YUV422则广泛应用于电视系统和模拟视频领域，能够提供更为丰富的色彩表现。 sensor.set_pixformat(sensor.RGB565) 一般都是设置为RGB565,做图像处理基本上都是用彩色的，虽然灰白也有。 set_regs:...

hackaday.io
Project | Portable Sound Visualization AR Device | Hackaday.io
8 de mayo de 2023 — The microphone array used in this project is the 6+1 microphone array from Sipeed. It has a total of 7 MEMS microphones mounted at the vertices and center of a hexagon, with 3 microphones arranged alo...

csdn.net
【01Studio MaixPy AI K210】8.串口通信 - CSDN博客
22 de febrero de 2022 — 本文详细介绍了如何使用USB转TTL串口、01Studio K210核心板进行串口硬件连接、软件配置，包括UART库的使用、引脚注册和初始化，提供了一个实例演示了如何通过串口进行数据收发，适合初学者快速上手串口编程。

luffca.com
Acoustic Beamforming using a Sipeed R6+1 Microphone Array
17 de diciembre de 2021 — In the MIC_ARRAY library of MaixPy, there is a function called get_map that performs sound source localization using the Sipeed R6+1 microphone array. This function outputs the sound level in the 8 x...
dfrobot.com.cn
【MaixPy快速上手】屏幕和摄像头的使用 DF创客社区
6 de mayo de 2021 — import sensor, lcd: 首先导入内置的 sensor （摄像头）库和 lcd （屏幕）库 sensor.reset(): 初始化摄像头，这里失败需要检查硬件 sensor.set_pixformat(sensor.RGB565): 设置摄像头为 RGB565 格式，默认都是用 RGB565 即可 sensor.set_framesize(sensor.QVGA): 分辨率为 QVG...

seeedstudio.com
Maix Cube helloworld - Hardware Products for AIoT Applications - Seeed ...
8 de noviembre de 2020 — Hello, I just received the Maix Cube and upon trying out the example code in the MaixPy IDE I get a distorted image in the LCD. See attached picture. Is the LCD not specified correctly in the program?...

csdn.net
K210_MaixPy IDE外设开发之六 串口UART接发以及接受控制LED
5 de octubre de 2020 — 本文介绍了如何在MaixPy IDE环境下，利用K210 AIR VR3版开发板的UART接口与电脑进行通信，通过接收AT指令控制GPIO驱动LED灯的亮灭。 教程包括了必要的库引用、代码编写和串口操作步骤。
randomnerdtutorials.com
Change ESP32-CAM OV2640 Camera Settings: Brightness, Resolution ...
8 de marzo de 2020 — This guide shows how to change the ESP32-CAM OV2640 camera settings such as contrast, brightness, resolution, quality, saturation and more using Arduino IDE.

arduinoraspi.blogspot.com
Hooking up the 6 + 1 Mic Array to the MaiX BiT - Blogger
30 de abril de 2019 — Sipeed offers a microphone array board with 7 mics and 12 RGB LEDs. Unfortunately the mic array, which SeeedStudio indicates is for Dock/Go/Bit, there is no real provisions made for the newer BiT boar...

sipeed.com
Sipeed Microphone - Sipeed Wiki
Sipeed Mic-Array Mic-Array microphone array, as of MaixPy version MicroPython v0.5.0-218-g8053a70, the pin io on the microphone array hardware supports custom configuration

sipeed.com
lcd (screen display) - Sipeed Wiki
roi is a rectangular tuple (x, y, w, h) of a region of interest. If not specified, it is the image rectangle. If the roi width is smaller than the lcd width, use a vertical black border to center the...

sipeed.com
sensor (camera) - Sipeed Wiki
Used to set the output frame size of the camera, k210 supports the maximum VGA format, and the image cannot be obtained if it is larger than VGA. The screen configured on the MaixPy development board...

sipeed.com
image (machine vision) - Sipeed Wiki
This method will also modify the basic image pixels and change the image size in bytes, so it can only be performed on grayscale images or RGB565 images. Otherwise, copy must be True to create a new m...

sipeed.com
drawing and writing - Sipeed Wiki
First, use the lcd module to draw directly on the screen. For more functions and parameters, please refer to lcd API Manual. 2. Second, use the image module to draw in the memory, and use the lcd.disp...

sipeed.com
machine.UART - Sipeed Wiki
The uart module is mainly used to drive the asynchronous serial port on the development board, and uart can be configured freely. There are 3 uarts in k210, and each uart can be freely mapped.

sipeed.com
Use of UART - Sipeed Wiki
For details on UART, please refer to UART-API Document 1. Instructions Import UART module from machine ... The pin used for configuration is UART function ... Create UART object ... Read and write dat...
github.com
sipeed_wiki/docs/soft/maixpy/en/develop_kit_board/module_microphone.md ...
Mic-Array microphone array, as of MaixPy version MicroPython v0.5.0-218-g8053a70, the pin io on the microphone array hardware supports custom configuration. Sound source localization.
github.com
sipeed_wiki/docs/hardware/en/modules/micarray.md at main - GitHub
Sipeed microphone array consists of six microphones along the board and a center microphone. The 12 leds on the array board can be used to visualize and identify the location of the sound source, whic...
github.com
panda-board/MaixPy: Micropython env for Sipeed Maix boards - GitHub
Micropython env for Sipeed Maix boards. Contribute to panda-board/MaixPy development by creating an account on GitHub.
github.com
GitHub - sipeed/MaixPy-v1: MicroPython for K210 RISC-V, let's play with ...
Maixpy is designed to make AIOT programming easier, based on the Micropython syntax, running on a very powerful embedded AIOT chip K210. There are many things you can do with MaixPy, please refer to h...
github.com
sipeed_wiki/docs/soft/maixpy/en/course/image/basic/draw.md at main ...
First, use the lcd module to draw directly on the screen import image, lcd lcd. init () lcd. draw_string (0, 0, "hello") For more functions and parameters, please refer to lcd API Manual
github.com
canmv/README.md at main · kendryte/canmv · GitHub
CanMV is designed to make AIOT programming easier, based on the Micropython syntax, running on the powerful embedded AI SOC series from Canaan. Currently it's running on K210. CanMV Boards configuatio...
github.com
MaixPy/maix/v1/machine/uart.py at main · sipeed/MaixPy
Easily create AI projects with Python on edge device - MaixPy/maix/v1/machine/uart.py at main · sipeed/MaixPy
seeedstudio.com
Microphone Array Sipeed MAIX R6+1 - files.seeedstudio.com
Sipeed MAIX R6+1 Microphone Array Sipeed 6+1 Microphone Arra is a 6 microphone expansion board for Maix AI development boards desig. ed for AI and voice applications. Including 6+1 digital microphones...

seeedstudio.com
Sipeed-6-1-Microphone-Array-for-Dock-Go-Bit - Seeed Studio
Sipeed 6+1 Microphone Arra is a 6 microphone expansion board for Maix AI development boards designed for AI and voice applications. Including 6+1 digital microphones, 12 three-color LEDs, it supports...
micropython.org
MicroPython tutorial for the pyboard
MicroPython tutorial for the pyboard This tutorial is intended to get you started with your pyboard. All you need is a pyboard and a micro-USB cable to connect it to your PC. If it is your first time,...
micropython.org
MicroPython - Python for microcontrollers
Firmware for various microcontroller ports and boards are built automatically on a daily basis and can be found below. WeAct F411 'blackpill'. Default variant is v3.1 with no SPI Flash.
micropython.org
class LCD – LCD control for the LCD touch-sensor pyskin
Set the contrast of the LCD. Valid values are between 0 and 47. Fill the screen with the given colour (0 or 1 for white or black). This method writes to the hidden buffer. Use show() to show the buffe...
micropython.org
class UART – duplex serial communication bus - MicroPython
The SAMD port’s UART.IRQ_TXIDLE is triggered while the last character is sent. On STM32F4xx MCU’s, using the trigger UART.IRQ_RXIDLE the handler will be called once after the first character and then...

openmv.io
sensor — camera sensor - OpenMV MicroPython 1.28 documentation
The function names follow the older set_pixformat / set_framesize style. Each function corresponds one-to-one to a method on csi.CSI; see the csi module for the complete capability set and per-argumen...

programmerclick.com
K210 Combate Real Tres Serial Recibir experimentos
Antes de usar UART, debemos usar FM para mapear y administrar el pin de chip. Como se muestra a continuación, configure el PIN10 en los pines de envío de UART2 y establezca el pin de recepción del PIN...

programmerclick.com
K210 —— Comunicación en serie UART - programador clic
Comunicación y modificación en serie de UART Con respecto a la forma de comunicación en serie, hay tres tipos principales en MSP430F5529, que son: UART, IIC y SPI.

m5stack.com
M5StickV MaixPy Getting Started Guide - m5stack-store
MaixPy IDE allows you to easily edit, upload and execute scripts in real time, as well as monitor camera images and transfer files in real time.

waveshare.com
Maix R6+1 Microphone Array - Waveshare Wiki
The Maix R6+1 Microphone Array module features 6+1 digital microphones and 12 RGB LEDs onboard, compatible with Maix AIoT series development boards. It is an ideal choice for voice-related application...

kendryte.com
maix.KPU - NEW — K210 CanMV
KPU是通用的神经网络处理器，它可以在低功耗的情况下实现卷积神经网络计算，时时获取被检测目标的大小、坐标和种类，对人脸或者物体进行检测和分类。 和 flash加载 方式只能二选一，不需要关键词，直接传参即可. 文件系统加载： 若图像不是由 sensor.snapshot() 获得，则需要执行 img.pix_to_ai() 进行转换. 如果图像大小与模型输入要求不一致，会返回 OsError. 返...

dfrobot.com
6+1 Microphone Array - DFRobot
Sipeed 6+1 Microphone Array 6-microphone expansion board for Maix AI development boards designed for AI and voice applications. Including 6+1 digital microphones, 12 three-color LEDs, it supports soun...
neven7.eu
Sipeed MAIX R6+1 Microphone Array - AI Application Kit
The Sipeed 6+1 microphone kit/array is an expanded board with 6 microphones for Maix AI development boards designed for AI and voice applications. It includes 6+1 digital microphones, 12 tri-color LED...

rotorxpress.com
Sipeed 6+1 Microphone Array for MAiX Dock/Go/Bit
Sipeed 6+1 Microphone Arra is a 6 microphone expansion board for Maix AI development boards designed for AI and voice applications. Including 6+1 digital microphones, 12 three-color LEDs, it supports...

made-in-china.com
Array de micrófonos Sipeed Maix R6+1 Micrófonos digitales y 6+1 LEDs ...
Array de micrófonos Sipeed Maix R6+1 Micrófonos digitales y 6+1 LEDs RGB compatibles con la serie Maix Aiot 12
arrow.com
Sipeed-6-1-Microphone-Array-for-Dock-Go-Bit - Seeed Studio
It support FPIOA, GPIO, TIMER, PWM, Flash, OV2640, LCD, etc. And it have zmodem, vi, SPIFFS on it, you can edit python directly or sz/rz file to board. We are glad to see you contribute for it:
instructables.com
content.instructables.com
os.mkdir('/sd/image') lcd.init() # Init lcd display lcd.clear(lcd.RED) # Clear lcd screen. # sensor.reset(dual_buff=True) # improve fps
