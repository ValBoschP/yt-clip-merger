import os
import subprocess
import threading
import shutil
import customtkinter as ctk
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================
# CONFIGURACIÓN GUI
# ========================
ctk.set_appearance_mode("Dark")  # Modos: "System" (estándar), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue" (estándar), "green", "dark-blue"

# ========================
# CONSTANTES
# ========================
CARPETA_DESCARGAS = "clips_descargados"
CARPETA_NORMALIZADOS = "clips_normalizados"
ARCHIVO_LISTA = "lista_ffmpeg.txt"
SALIDA = "video_final.mp4"
MAX_HILOS = 4
RESOLUCION_MAX = 1080
FRAMERATE = 60

class VideoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("yt-clip-merger")
        self.geometry("700x600")

        # --- GRID LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # El log se expande

        # 1. Título y Descripción
        self.label_titulo = ctk.CTkLabel(self, text="YT-CLIP-MERGER", font=("Roboto", 24, "bold"))
        self.label_titulo.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 2. Área de Enlaces (Input)
        self.frame_input = ctk.CTkFrame(self)
        self.frame_input.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.label_instruccion = ctk.CTkLabel(self.frame_input, text="Pega aquí los enlaces (uno por línea):")
        self.label_instruccion.pack(anchor="w", padx=10, pady=5)

        self.textbox_links = ctk.CTkTextbox(self.frame_input, height=150)
        self.textbox_links.pack(fill="x", padx=10, pady=(0, 10))

        # 3. Botón de Acción
        self.boton_iniciar = ctk.CTkButton(self, text="INICIAR PROCESO", command=self.iniciar_proceso_hilo, height=50, font=("Roboto", 16))
        self.boton_iniciar.grid(row=2, column=0, padx=20, pady=10)

        # 4. Consola de Salida (Log)
        self.textbox_log = ctk.CTkTextbox(self, state="disabled", fg_color="#1c1c1c", text_color="#00ff00", font=("Consolas", 12))
        self.textbox_log.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Mensaje inicial
        self.log_mensaje("Bienvenido. Pega los links arriba y dale a Iniciar.")

    def log_mensaje(self, mensaje):
        """Escribe en la consola de la GUI de forma segura."""
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", mensaje + "\n")
        self.textbox_log.see("end") # Autoscroll al final
        self.textbox_log.configure(state="disabled")

    def iniciar_proceso_hilo(self):
        """Ejecuta la lógica en un hilo separado para no congelar la GUI."""
        self.boton_iniciar.configure(state="disabled", text="Procesando... (Espera)")
        hilo = threading.Thread(target=self.ejecutar_logica)
        hilo.start()

    # ========================
    # LÓGICA DEL PROGRAMA
    # ========================
    def ejecutar_logica(self):
        # 1. Obtener enlaces del textbox
        texto_links = self.textbox_links.get("1.0", "end")
        enlaces_crudos = [line.strip() for line in texto_links.split("\n") if line.strip()]

        if not enlaces_crudos:
            self.log_mensaje("❌ Error: No has pegado ningún enlace.")
            self.boton_iniciar.configure(state="normal", text="INICIAR PROCESO")
            return

        # Eliminar duplicados
        enlaces = list(dict.fromkeys(enlaces_crudos))
        duplicados = len(enlaces_crudos) - len(enlaces)
        if duplicados > 0:
            self.log_mensaje(f"Eliminados {duplicados} enlaces repetidos.")

        # Crear carpetas
        os.makedirs(CARPETA_DESCARGAS, exist_ok=True)
        os.makedirs(CARPETA_NORMALIZADOS, exist_ok=True)
        os.makedirs("yt_cache", exist_ok=True)

        self.log_mensaje(f"Descargando {len(enlaces)} videos...")

        # Descargar
        resultados = []
        with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
            futures = [executor.submit(self.descargar_clip, i, enlace) for i, enlace in enumerate(enlaces, 1)]
            for future in as_completed(futures):
                resultados.append(future.result())

        resultados.sort(key=lambda x: x[0])
        rutas_descargadas = [ruta for _, ruta in resultados if ruta]

        if not rutas_descargadas:
            self.log_mensaje("❌ Fallaron todas las descargas.")
            self.boton_iniciar.configure(state="normal", text="INICIAR PROCESO")
            return

        self.log_mensaje("Normalizando clips (esto puede tardar)...")

        # Normalizar
        normalizados = []
        for i, ruta in enumerate(rutas_descargadas, 1):
            _, ruta_norm = self.normalizar_clip(i, ruta)
            if ruta_norm:
                normalizados.append(ruta_norm)

        if not normalizados:
            self.log_mensaje("❌ Error al normalizar.")
            self.boton_iniciar.configure(state="normal", text="INICIAR PROCESO")
            return

        # Unir
        with open(ARCHIVO_LISTA, "w", encoding="utf-8") as f:
            for ruta in normalizados:
                f.write(f"file '{os.path.abspath(ruta)}'\n")

        self.log_mensaje("Uniendo video final...")
        
        comando_union = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ARCHIVO_LISTA, "-c", "copy", SALIDA
        ]
        
        try:
            # En Windows subprocess necesita shell=True a veces, en Linux no suele hacer falta para esto
            # Si da error de 'file not found' en ffmpeg, asegúrate que ffmpeg está en la carpeta o PATH
            creation_flags = 0
            if os.name == 'nt': # Si es windows, evitar ventana negra emergente
                 creation_flags = subprocess.CREATE_NO_WINDOW
            
            subprocess.run(comando_union, check=True, creationflags=creation_flags)
            self.log_mensaje(f"✅ Video creado: {SALIDA}")
            self.limpiar_temporales()
        except Exception as e:
            self.log_mensaje(f"❌ Error uniendo video: {e}")

        self.boton_iniciar.configure(state="normal", text="INICIAR PROCESO")

    # --- FUNCIONES INTERNAS ADAPTADAS ---
    def descargar_clip(self, i, enlace):
        ruta_salida = os.path.join(CARPETA_DESCARGAS, f"clip_{i}.mp4")
        
        # Configuración visual para Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        if os.name == 'nt':
            # EN WINDOWS: Buscamos el .exe en la carpeta (para modo portable)
            ejecutable_yt = "yt-dlp.exe"
            ejecutable_ffmpeg = "ffmpeg.exe"
            ruta_absoluta_ffmpeg = os.path.abspath(ejecutable_ffmpeg)
        else:
            # EN LINUX: Usamos los comandos globales del sistema (lo que acabas de instalar)
            ejecutable_yt = "./yt-dlp" # yt-dlp sí lo mantenemos local
            ejecutable_ffmpeg = "ffmpeg" # <--- Sin ruta, sin ./ (usa el del sistema)
            
            # En Linux, para usar el del sistema, usamos shutil.which o simplemente el nombre
            import shutil
            ruta_absoluta_ffmpeg = shutil.which("ffmpeg") 

        ruta_absoluta_yt = os.path.abspath(ejecutable_yt)
        
        comando = [
            ruta_absoluta_yt,
            "--ffmpeg-location", ruta_absoluta_ffmpeg,
            "-f", f"bestvideo[height<={RESOLUCION_MAX}]+bestaudio/best[height<={RESOLUCION_MAX}]",
            "--merge-output-format", "mp4",
            "-o", ruta_salida,
            enlace
        ]
        
        try:
            # Mantenemos el diagnóstico por si acaso
            resultado = subprocess.run(
                comando, 
                check=True, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo
            )
            self.log_mensaje(f"✅ Clip {i} descargado.")
            return i, ruta_salida

        except subprocess.CalledProcessError as e:
            self.log_mensaje(f"⚠️ ERROR FATAL en Clip {i}:")
            self.log_mensaje(e.stderr)
            return i, None

    def normalizar_clip(self, i, ruta_entrada):
        ruta_salida = os.path.join(CARPETA_NORMALIZADOS, f"clip_norm_{i}.mp4")
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # LÓGICA DE SELECCIÓN
        if os.name == 'nt':
            cmd_ffmpeg = os.path.abspath("ffmpeg.exe")
        else:
            cmd_ffmpeg = "ffmpeg" # Usa el comando global de Linux

        comando = [
            cmd_ffmpeg, 
            "-y", "-i", ruta_entrada,
            "-vf", f"scale=-2:{RESOLUCION_MAX},fps={FRAMERATE}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", ruta_salida
        ]
        try:
            subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            self.log_mensaje(f"🔧 Clip {i} normalizado.")
            return i, ruta_salida
        except:
            self.log_mensaje(f"⚠️ Falló normalizar clip {i}")
            return i, None
    
    def limpiar_temporales(self):
        """Borra las carpetas y archivos intermedios para dejar todo limpio."""
        self.log_mensaje("Limpiando archivos temporales...")
        
        carpetas_a_borrar = [CARPETA_DESCARGAS, CARPETA_NORMALIZADOS, "yt_cache"]
        archivos_a_borrar = [ARCHIVO_LISTA]

        # Borrar carpetas
        for carpeta in carpetas_a_borrar:
            if os.path.exists(carpeta):
                try:
                    shutil.rmtree(carpeta) # rmtree borra la carpeta y todo lo de adentro
                except Exception as e:
                    print(f"No se pudo borrar {carpeta}: {e}")

        # Borrar archivo de lista
        for archivo in archivos_a_borrar:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                except Exception as e:
                    print(f"No se pudo borrar {archivo}: {e}")
        
        self.log_mensaje("¡Limpieza completada! Solo queda el video final.")

if __name__ == "__main__":
    app = VideoApp()
    app.mainloop()