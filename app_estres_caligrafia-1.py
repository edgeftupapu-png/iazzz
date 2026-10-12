"""
APP DETECTOR DE ESTRÉS POR CALIGRAFÍA
Funciona offline en Android
Autor: Osmar Josias Lima Cahuaya
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.garden.camera import Camera
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import cv2
import numpy as np
import joblib
from datetime import datetime
import os
from android.permissions import request_permissions, Permission
from android.storage import primary_external_storage_path

# Configurar tamaño de ventana
Window.size = (1080, 1920)

class ExtractorCaracteristicas:
    """Extrae características caligráficas de una imagen"""
    
    @staticmethod
    def extraer(imagen_path):
        """
        Extrae 5 características de una imagen de caligrafía
        
        Retorna: [inclinacion, presion, densidad, varianza_altura, margen]
        """
        # Leer imagen
        img = cv2.imread(imagen_path)
        if img is None:
            return None
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Binarizar con Otsu
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 1. INCLINACIÓN (análisis de orientación de trazos)
        # Usar transformada de Hough para detectar líneas
        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        inclinacion = 0
        if lines is not None and len(lines) > 0:
            angulos = [line[0][1] for line in lines[:10]]
            inclinacion = float(np.mean(np.rad2deg(angulos)) - 90)
        
        # 2. PRESIÓN (densidad de píxeles negros en la imagen)
        presion = float(np.sum(binary == 0) / binary.size)
        
        # 3. DENSIDAD DE TINTA (proporción de píxeles de trazo)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        densidad = float(np.sum(dilated == 0) / dilated.size)
        
        # 4. VARIANZA DE ALTURA (análisis de proyección vertical)
        proyeccion_y = np.sum(binary == 0, axis=1)
        varianza_altura = float(np.var(proyeccion_y))
        
        # 5. MARGEN IZQUIERDO (píxeles en blanco antes del primer trazo)
        proyeccion_x = np.sum(binary == 0, axis=0)
        primer_trazo = np.where(proyeccion_x > 0)[0]
        margen = float(primer_trazo[0]) if len(primer_trazo) > 0 else 0
        
        # Normalizar margen
        margen = (margen / binary.shape[1]) * 100
        
        # Normalizar varianza de altura
        varianza_altura = (varianza_altura / np.max(proyeccion_y)) * 100 if np.max(proyeccion_y) > 0 else 0
        
        return [inclinacion, presion, densidad, varianza_altura, margen]


class AppEstresCaligrafiaUI(BoxLayout):
    """Interfaz de usuario principal"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Cargar modelo
        try:
            self.modelo = joblib.load('/storage/emulated/0/modelo_estres.joblib')
            self.feature_names = joblib.load('/storage/emulated/0/feature_names.joblib')
        except:
            # Fallback si no está en la ruta esperada
            self.modelo = None
            self.feature_names = ['inclinacion', 'presion', 'densidad', 'varianza_altura', 'margen']
        
        self.extractor = ExtractorCaracteristicas()
        self.ultima_imagen = None
        self.resultado = None
        
        # ═══════════════════════════════════════════════════════════════════════
        # ENCABEZADO
        # ═══════════════════════════════════════════════════════════════════════
        header = BoxLayout(orientation='vertical', size_hint_y=0.15)
        
        titulo = Label(
            text='[b]DETECTOR DE ESTRÉS[/b]\n[i]Por Análisis de Caligrafía[/i]',
            markup=True,
            font_size='20sp'
        )
        header.add_widget(titulo)
        
        subtitulo = Label(
            text='Colegio Nazareno Basil Miller',
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        header.add_widget(subtitulo)
        self.add_widget(header)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ÁREA DE CÁMARA / IMAGEN
        # ═══════════════════════════════════════════════════════════════════════
        self.camera_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
        
        # Placeholder de imagen
        self.img_display = Image(
            source='data/images/defaultimage.png',
            size_hint_y=0.85
        )
        self.camera_box.add_widget(self.img_display)
        
        # Botón de cámara
        btn_camera = Button(
            text='📷 TOMAR FOTO',
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 0.8, 1),
            font_size='14sp'
        )
        btn_camera.bind(on_press=self.tomar_foto)
        self.camera_box.add_widget(btn_camera)
        
        self.add_widget(self.camera_box)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ÁREA DE RESULTADO
        # ═══════════════════════════════════════════════════════════════════════
        self.resultado_box = BoxLayout(orientation='vertical', size_hint_y=0.35)
        
        self.label_resultado = Label(
            text='[b]Resultado:[/b]\nEsperando foto...',
            markup=True,
            font_size='16sp',
            size_hint_y=0.5
        )
        self.resultado_box.add_widget(self.label_resultado)
        
        # Características extraídas
        self.label_caracteristicas = Label(
            text='[b]Características:[/b]\nPresión: -\nDensidad: -\nInclinación: -\nVarianza: -\nMargen: -',
            markup=True,
            font_size='11sp',
            size_hint_y=0.4
        )
        self.resultado_box.add_widget(self.label_caracteristicas)
        
        # Botón de análisis
        btn_analizar = Button(
            text='🔍 ANALIZAR',
            size_hint_y=0.1,
            background_color=(0.2, 0.8, 0.4, 1),
            font_size='14sp'
        )
        btn_analizar.bind(on_press=self.analizar)
        self.resultado_box.add_widget(btn_analizar)
        
        self.add_widget(self.resultado_box)
    
    def tomar_foto(self, instance):
        """Abre la cámara para capturar foto"""
        # En dispositivo real, esto abre la cámara nativa
        # Por ahora, cargamos una imagen de prueba
        
        try:
            # Ruta de almacenamiento
            storage_path = primary_external_storage_path()
            foto_path = os.path.join(storage_path, 'DCIM', 'Camera', 'estres_muestra.jpg')
            
            # Si existe, cargarla
            if os.path.exists(foto_path):
                self.ultima_imagen = foto_path
                self.img_display.source = foto_path
                self.label_resultado.text = '[b]Foto cargada[/b]\nHaz click en ANALIZAR'
        except:
            self.label_resultado.text = '[b]Error[/b]\nNo se pudo acceder a la cámara'
    
    def analizar(self, instance):
        """Analiza la foto y predice estrés"""
        if self.ultima_imagen is None:
            self.label_resultado.text = '[b]⚠️ Error[/b]\nPrimero toma una foto'
            return
        
        try:
            # Extraer características
            caracteristicas = self.extractor.extraer(self.ultima_imagen)
            
            if caracteristicas is None:
                self.label_resultado.text = '[b]⚠️ Error[/b]\nNo se puede procesar la imagen'
                return
            
            # Mostrar características
            inc, pres, dens, var, mar = caracteristicas
            self.label_caracteristicas.text = (
                f'[b]Características:[/b]\n'
                f'Presión: {pres:.2f}\n'
                f'Densidad: {dens:.2f}\n'
                f'Inclinación: {inc:.1f}°\n'
                f'Varianza: {var:.1f}\n'
                f'Margen: {mar:.1f}px'
            )
            
            # Predecir con modelo
            if self.modelo is not None:
                prediccion = self.modelo.predict([caracteristicas])[0]
                probabilidades = self.modelo.predict_proba([caracteristicas])[0]
                
                # Mapear resultado
                clases = ['bajo', 'moderado', 'alto']
                clase_idx = list(self.modelo.classes_).index(prediccion)
                confianza = probabilidades[clase_idx]
                
                # Colorear según resultado
                if prediccion == 'bajo':
                    color_bg = '[color=00ff00]'
                    emoji = '✅'
                elif prediccion == 'moderado':
                    color_bg = '[color=ffaa00]'
                    emoji = '⚠️'
                else:
                    color_bg = '[color=ff0000]'
                    emoji = '🔴'
                
                self.label_resultado.text = (
                    f'{color_bg}[b]{emoji} ESTRÉS: {prediccion.upper()}[/b][/color]\n'
                    f'Confianza: {confianza:.0%}\n'
                    f'[size=10sp]{datetime.now().strftime("%d/%m/%Y %H:%M")}[/size]'
                )
                
                self.resultado = {
                    'nivel': prediccion,
                    'confianza': confianza,
                    'caracteristicas': caracteristicas,
                    'timestamp': datetime.now()
                }
            else:
                self.label_resultado.text = '[b]⚠️[/b]\nModelo no cargado'
        
        except Exception as e:
            self.label_resultado.text = f'[b]Error:[/b]\n{str(e)}'


class AppEstresCaligrafiaApp(App):
    """Aplicación principal"""
    
    def build(self):
        self.title = 'Detector de Estrés - Caligrafía IA'
        
        # Solicitar permisos
        request_permissions([
            Permission.CAMERA,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])
        
        return AppEstresCaligrafiaUI()


if __name__ == '__main__':
    AppEstresCaligrafiaApp().run()
