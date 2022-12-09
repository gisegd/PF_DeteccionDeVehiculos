'''
Array de Verdes: esquinas --> convertir a N mascaras individuales 
Array de Rojos: auto_Rects --> convertir a M mascaras individuales
Por cada uno de los rojos se observa en cuál verde coincide (itera con cada rojo por los verdes)
Si coincide con un verde se agrega un 1 en la tabla (excluyendo los de menos de la mitad del área)

Cada M and N --> Coinciden --> Verificar áreas: 
                 Si Ar*Av (intersección) < Av/4 --> No coincide
                 Si Ar*Av (intersección) >= Av/4 --> Coincide

V/R 0  1  2  3  4  5  6  7  8
0   1  0  0  0  0  0  0  0  0
1   0  1  0  0  0  0  0  0  0
2   0  0  0  1  0  0  0  0  0
3   0  0  0  0  1  0  0  0  0
4   0  0  1  0  0  0  0  0  0
5   0  0  0  0  0  1  1  0  0
6   0  0  0  0  0  0  0  0  0
7   0  0  0  0  0  0  0  0  1
8   0  0  0  0  0  0  0  0  1

Col vacia = FP (R 7)
Columna con 1 = VP 
Columna con >1 = FP (R 8)
Fil vacia = FN (V 6)
Fila con >1 = VPd (V 5) 

'''

#Documentacion de Python:
#"The xml.etree.ElementTree module implements a simple and efficient API for parsing and creating XML data.""
#https://docs.python.org/3/library/xml.etree.elementtree.html
import xml.etree.ElementTree as ET
import cv2 as CV #OpenCV
#Librería para expresiones regulares
import re
#Librerías para acceder a funciones del sistema operativo y operar sobre patrones de nombres de archivos
import glob, os
#Librería para cálculo numérico avanzado
import numpy
from decimal import Decimal
#Librería para acceder a funciones del sistema
import sys
#Librería para conversión de formatos YOLO
import pybboxes as pbx

#Directorios del DataSet
carpetaAnotaciones='Anotaciones_Imagenes_Prueba'
carpetaImagenes='Imagenes_Prueba'
resultadosYOLO = 'ResultadosYOLO_M30HD'
#Sizes para el detectMultiScale
minSize = 30
maxSize = 70 
#Tamaño de la imagen 
alto = 720 
ancho = 1200 
#Recorte de la parte inferior y superior (medido desde arriba)
recorteYsup = 130
recorteYinf = 550
recorteX = 250

#Bloque que ordena los nombres de los archivos de imágenes y sus anotaciones de forma descendente 
#para lograr coincidencia de índices al recorrer las carpetas (de lo contrario están ordenados alfabéticamente)
#y coincidencia entre el nombre de imagen y su índice.
numeros = re.compile(r'(\d+)')
def numericalSort(value):
    partes = numeros.split(value)
    partes[1::2] = map(int, partes[1::2])
    return partes

xmls=sorted(glob.glob(os.path.join(carpetaAnotaciones, '*.xml')), key=numericalSort)
imagenes=sorted(glob.glob(os.path.join(carpetaImagenes, '*.jpg')), key=numericalSort) 
txts=sorted(glob.glob(os.path.join(resultadosYOLO, '*.txt')), key=numericalSort)    

#Se inicializa el archivo de resultados
resultados = open("resultadosYOLOM30HD.txt", "w")
resultados.close()
resultados = open("resultadosYOLOM30HD.txt", "a")
resultados.write('ID,Imagen,DataSet,VP,VPsinD,FP,FN\n')

x=1
for j in range(0, len(xmls), 10): #Se recorre la carpeta de anotaciones

    #Inicialización de Matrices: DataSet y Detecciones con el tamaño de la imagen
    matDataSet = (alto,ancho)
    matDataSet = numpy.zeros(matDataSet)
    matDetect = (alto,ancho)
    matDetect = numpy.zeros(matDetect)
    mascarasVerdes = []
    mascarasRojas = []

    #Se analiza como XML y se apunta al tag raíz
    tree = ET.parse(xmls[j])
    root = tree.getroot()
    #Array de array de 4 posiciones, cada ID -> [xmin, ymin, xmax, ymax]
    esquinas = [[]] 
    #Se recorre el árbol entre sus elementos y sub-elementos buscando el tag 'bndbox' y se cargan las esquinas
    i = 0
    for car in root.iter('object'):
        #if(car.find('class').text == 'motorbike' or car.find('class').text == 'van'):
        if(car.find('class').text == 'motorbike'): 
            continue
        box = car.find('bndbox')
        #Recorte inferior y superior
        if(int(box.find('ymin').text) < recorteYsup or int(box.find('ymax').text) > recorteYinf):
            continue
        esquinas[i].append(int(box.find('xmin').text)) 
        esquinas[i].append(int(box.find('ymin').text)) 
        esquinas[i].append(int(box.find('xmax').text))
        esquinas[i].append(int(box.find('ymax').text))
        i += 1
        esquinas.append([])
    esquinas.pop(i)
 
    #Se carga la imagen
    imagen = CV.imread(imagenes[j])

    #Se recorre la lista de ubicaciones de los vehículos
    for i in range(len(esquinas)):  
        #Matriz binaria del dataset
        matDataSet[esquinas[i][1]:esquinas[i][3],esquinas[i][0]:esquinas[i][2]] = 1
        #Array de Verdes: esquinas --> convertir a N mascaras individuales   
        mascarasVerdes.append((alto,ancho))
        mascarasVerdes[i] = numpy.zeros(mascarasVerdes[i])
        mascarasVerdes[i][esquinas[i][1]:esquinas[i][3],esquinas[i][0]:esquinas[i][2]] = 1

    autosYolo = []
    #Si el archivo existe se lee
    nImagen = j+4001
    if (f"{resultadosYOLO}\\image00{nImagen}.txt" in txts):
        #Se lee el archivo de cada imagen
        yoloFormat = open(f"{resultadosYOLO}\\image00{nImagen}.txt", "r")
        autosYolo = yoloFormat.read().splitlines()

    auto_Rects = []
    for auto in range (0,len(autosYolo)):
        autoCoord = autosYolo[auto].split()
        #Cada línea es un auto, se consideran las columnas 1-4
        autoYolo = (Decimal(autoCoord[1]), Decimal(autoCoord[2]), Decimal(autoCoord[3]), Decimal(autoCoord[4]))
        size = 1200, 720  # WxH of the image
        convToVOC = pbx.convert_bbox(autoYolo, from_type="yolo", to_type="voc", image_size=size)

        #convToVOC[0],convToVOC[1],convToVOC[2],convToVOC[3]
        #   xmin        ymin          xmax        ymax
        if(convToVOC[1] < recorteYsup-5 or convToVOC[3] > recorteYinf+5 or convToVOC[0] < recorteX):
            continue
        auto_Rects.append((convToVOC[0],convToVOC[1],convToVOC[2]-convToVOC[0],convToVOC[3]-convToVOC[1]))

    f = 0
    for (fX, fY, fW, fH) in auto_Rects:
        #Matriz binaria de detecciones
        matDetect[fY:fY+ fH, fX:fX + fW] = 1
        #Array de Rojos: auto_Rects --> convertir a M mascaras individuales
        mascarasRojas.append((alto,ancho))
        mascarasRojas[f] = numpy.zeros(mascarasRojas[f])
        mascarasRojas[f][fY:fY+ fH, fX:fX + fW] = 1
        f += 1

    matrizVR = (len(mascarasVerdes),len(mascarasRojas))
    matrizVR = numpy.zeros(matrizVR)

    # Cada M and N --> Coinciden --> Verificar áreas: 
    #                  Si Ar*Av (intersección) < Av/4 --> No coincide
    #                  Si Ar*Av (intersección) >= Av/4 --> Coincidencia
    deteccionesValidas = []
    for r in range(len(mascarasRojas)): 
        for v in range(len(mascarasVerdes)): 
            if(numpy.sum(mascarasRojas[r]*mascarasVerdes[v]) >= numpy.sum(mascarasVerdes[v])/4):
                if(numpy.sum(mascarasRojas[r]) >= numpy.sum(mascarasVerdes[v])/4):
                    matrizVR[v,r] = 1

    # Columna vacia = FP 
    # Columna con 1 = VP 
    # Columna con >1 = FP 
    # Fil vacia = FN 
    # Fila con >1 = VPd (Sum Fila-1: Duplicados a eliminar de VPsinD)
    VP = 0
    VPd = 0
    VPsinD = 0
    FP = 0
    FN = 0

    matrizVR_Col = numpy.sum(matrizVR, axis=0)
    matrizVR_Fil = numpy.sum(matrizVR, axis=1)

    for col in matrizVR_Col:
        if(col == 0):
            FP += 1
        elif (col == 1):
            VP += 1
            VPsinD += 1
        else:
            FP += 1

    for fil in matrizVR_Fil:
        if(fil == 0):
            FN += 1
        elif (fil > 1):
            VPd += fil
            VPsinD -= int(fil-1)

    resultados.write(str(x)+','+imagenes[j]+','+str(len(mascarasVerdes))+','+str(VP)+','+str(VPsinD)+','+str(FP)+','+str(FN)+'\n')
    print(imagenes[j])
    x += 1

resultados.close()