import os
import subprocess
import threading
import shutil
import customtkinter as ctk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog
import time

# ========================
# CONFIGURACIÓN GUI
# ========================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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
        self.title("YT Clip Merger")
        self.geometry("900x750")
        self.minsize(800, 650)

        # Variables de estado
        self.procesando = False
        self.total_videos = 0
        self.videos_completados = 0

        # --- GRID LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ========================
        # HEADER
        # ========================
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="ew")
        
        self.label_titulo = ctk.CTkLabel(
            self.frame_header, 
            text="🎬 YT Clip Merger", 
            font=("Roboto", 32, "bold"),
            text_color=("#2196F3", "#64B5F6")
        )
        self.label_titulo.pack()
        
        self.label_subtitulo = ctk.CTkLabel(
            self.frame_header,
            text="Descarga, normaliza y une clips de YouTube en un solo video",
            font=("Roboto", 14),
            text_color=("gray60", "gray50")
        )
        self.label_subtitulo.pack(pady=(5, 0))

        # ========================
        # ÁREA DE ENLACES
        # ========================
        self.frame_input = ctk.CTkFrame(self, corner_radius=15)
        self.frame_input.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        self.frame_input.grid_columnconfigure(0, weight=1)

        self.label_instruccion = ctk.CTkLabel(
            self.frame_input,
            text="📎 Enlaces de YouTube",
            font=("Roboto", 16, "bold"),
            anchor="w"
        )
        self.label_instruccion.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.label_info = ctk.CTkLabel(
            self.frame_input,
            text="Pega aquí los enlaces de los clips (uno por línea)",
            font=("Roboto", 12),
            text_color=("gray60", "gray50"),
            anchor="w"
        )
        self.label_info.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        self.textbox_links = ctk.CTkTextbox(
            self.frame_input,
            height=180,
            font=("Monospace", 11),
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30")
        )
        self.textbox_links.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        # ========================
        # OPCIONES Y CONTROLES
        # ========================
        self.frame_controles = ctk.CTkFrame(self, corner_radius=15)
        self.frame_controles.grid(row=2, column=0, padx=30, pady=10, sticky="ew")
        self.frame_controles.grid_columnconfigure((0, 1, 2), weight=1)

        # Selector de resolución
        self.label_res = ctk.CTkLabel(
            self.frame_controles,
            text="Resolución máxima:",
            font=("Roboto", 12)
        )
        self.label_res.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.combo_resolucion = ctk.CTkComboBox(
            self.frame_controles,
            values=["720p", "1080p", "1440p", "2160p (4K)"],
            width=150,
            state="readonly"
        )
        self.combo_resolucion.set("1080p")
        self.combo_resolucion.grid(row=0, column=0, padx=(160, 15), pady=15, sticky="w")

        # Botón principal
        self.boton_iniciar = ctk.CTkButton(
            self.frame_controles,
            text="▶ INICIAR PROCESO",
            command=self.iniciar_proceso_hilo,
            height=45,
            font=("Roboto", 16, "bold"),
            corner_radius=10,
            fg_color=("#2196F3", "#1976D2"),
            hover_color=("#1976D2", "#1565C0")
        )
        self.boton_iniciar.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        # Botón limpiar
        self.boton_limpiar = ctk.CTkButton(
            self.frame_controles,
            text="🗑 Limpiar",
            command=self.limpiar_campos,
            height=45,
            font=("Roboto", 14),
            corner_radius=10,
            fg_color=("gray60", "gray40"),
            hover_color=("gray50", "gray35"),
            width=120
        )
        self.boton_limpiar.grid(row=0, column=2, padx=15, pady=15, sticky="e")

        # ========================
        # BARRA DE PROGRESO
        # ========================
        self.frame_progreso = ctk.CTkFrame(self, corner_radius=15)
        self.frame_progreso.grid(row=3, column=0, padx=30, pady=10, sticky="ew")
        self.frame_progreso.grid_columnconfigure(0, weight=1)

        self.label_estado = ctk.CTkLabel(
            self.frame_progreso,
            text="Estado: Esperando",
            font=("Roboto", 13),
            anchor="w"
        )
        self.label_estado.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.progressbar = ctk.CTkProgressBar(
            self.frame_progreso,
            height=8,
            corner_radius=4
        )
        self.progressbar.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.progressbar.set(0)

        # ========================
        # CONSOLA DE LOG
        # ========================
        self.frame_log = ctk.CTkFrame(self, corner_radius=15)
        self.frame_log.grid(row=4, column=0, padx=30, pady=(10, 30), sticky="nsew")
        self.frame_log.grid_columnconfigure(0, weight=1)
        self.frame_log.grid_rowconfigure(1, weight=1)

        self.label_log = ctk.CTkLabel(
            self.frame_log,
            text="📋 Log del proceso",
            font=("Roboto", 14, "bold"),
            anchor="w"
        )
        self.label_log.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.textbox_log = ctk.CTkTextbox(
            self.frame_log,
            state="disabled",
            font=("Monospace", 11),
            corner_radius=10,
            fg_color=("#1a1a1a", "#0a0a0a"),
            text_color=("#00ff88", "#00ff88"),
            border_width=1,
            border_color=("gray70", "gray30")
        )
        self.textbox_log.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        
        # Mensaje inicial
        self.log_mensaje("✨ Bienvenido a YT Clip Merger")
        self.log_mensaje("💡 Pega los enlaces de YouTube arriba y presiona 'Iniciar Proceso'")
        self.log_mensaje("")

    def log_mensaje(self, mensaje):
        """Escribe en la consola de la GUI de forma segura."""
        timestamp = time.strftime("%H:%M:%S")
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", f"[{timestamp}] {mensaje}\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def actualizar_estado(self, texto, progreso=None):
        """Actualiza el estado y la barra de progreso."""
        self.label_estado.configure(text=f"Estado: {texto}")
        if progreso is not None:
            self.progressbar.set(progreso)

    def limpiar_campos(self):
        """Limpia el área de texto y resetea la interfaz."""
        if not self.procesando:
            self.textbox_links.delete("1.0", "end")
            self.actualizar_estado("Esperando", 0)
            self.log_mensaje("🧹 Campos limpiados")

    def iniciar_proceso_hilo(self):
        """Ejecuta la lógica en un hilo separado para no congelar la GUI."""
        if self.procesando:
            return
            
        self.procesando = True
        self.boton_iniciar.configure(
            state="disabled",
            text="⏳ Procesando...",
            fg_color=("gray60", "gray40")
        )
        self.boton_limpiar.configure(state="disabled")
        self.combo_resolucion.configure(state="disabled")
        
        hilo = threading.Thread(target=self.ejecutar_logica, daemon=True)
        hilo.start()

    def finalizar_proceso(self):
        """Restaura la interfaz al estado inicial."""
        self.procesando = False
        self.boton_iniciar.configure(
            state="normal",
            text="▶ INICIAR PROCESO",
            fg_color=("#2196F3", "#1976D2")
        )
        self.boton_limpiar.configure(state="normal")
        self.combo_resolucion.configure(state="readonly")

    # ========================
    # LÓGICA DEL PROGRAMA
    # ========================
    def ejecutar_logica(self):
        try:
            # Obtener resolución seleccionada
            res_map = {"720p": 720, "1080p": 1080, "1440p": 1440, "2160p (4K)": 2160}
            res_texto = self.combo_resolucion.get()
            global RESOLUCION_MAX
            RESOLUCION_MAX = res_map[res_texto]

            # 1. Obtener enlaces del textbox
            self.actualizar_estado("Procesando enlaces", 0.05)
            texto_links = self.textbox_links.get("1.0", "end")
            enlaces_crudos = [line.strip() for line in texto_links.split("\n") if line.strip()]

            if not enlaces_crudos:
                self.log_mensaje("❌ Error: No has pegado ningún enlace")
                self.actualizar_estado("Error: Sin enlaces", 0)
                self.finalizar_proceso()
                return

            # Eliminar duplicados
            enlaces = list(dict.fromkeys(enlaces_crudos))
            duplicados = len(enlaces_crudos) - len(enlaces)
            if duplicados > 0:
                self.log_mensaje(f"🔄 Eliminados {duplicados} enlaces duplicados")

            self.total_videos = len(enlaces)
            self.videos_completados = 0

            # Crear carpetas
            os.makedirs(CARPETA_DESCARGAS, exist_ok=True)
            os.makedirs(CARPETA_NORMALIZADOS, exist_ok=True)
            os.makedirs("yt_cache", exist_ok=True)

            self.log_mensaje(f"📥 Iniciando descarga de {len(enlaces)} videos...")
            self.actualizar_estado(f"Descargando {len(enlaces)} videos", 0.1)

            # Descargar
            resultados = []
            with ThreadPoolExecutor(max_workers=MAX_HILOS) as executor:
                futures = [executor.submit(self.descargar_clip, i, enlace) for i, enlace in enumerate(enlaces, 1)]
                for future in as_completed(futures):
                    resultados.append(future.result())
                    self.videos_completados += 1
                    progreso = 0.1 + (self.videos_completados / self.total_videos) * 0.3
                    self.actualizar_estado(
                        f"Descargando: {self.videos_completados}/{self.total_videos}",
                        progreso
                    )

            resultados.sort(key=lambda x: x[0])
            rutas_descargadas = [ruta for _, ruta in resultados if ruta]

            if not rutas_descargadas:
                self.log_mensaje("❌ Error: Fallaron todas las descargas")
                self.actualizar_estado("Error en descargas", 0)
                self.finalizar_proceso()
                return

            self.log_mensaje(f"✅ Descargados {len(rutas_descargadas)}/{len(enlaces)} videos")
            self.log_mensaje("🔧 Normalizando clips...")
            self.actualizar_estado("Normalizando clips", 0.45)

            # Normalizar
            self.videos_completados = 0
            normalizados = []
            for i, ruta in enumerate(rutas_descargadas, 1):
                _, ruta_norm = self.normalizar_clip(i, ruta)
                if ruta_norm:
                    normalizados.append(ruta_norm)
                self.videos_completados += 1
                progreso = 0.45 + (self.videos_completados / len(rutas_descargadas)) * 0.3
                self.actualizar_estado(
                    f"Normalizando: {self.videos_completados}/{len(rutas_descargadas)}",
                    progreso
                )

            if not normalizados:
                self.log_mensaje("❌ Error al normalizar clips")
                self.actualizar_estado("Error en normalización", 0)
                self.finalizar_proceso()
                return

            # Unir
            self.log_mensaje("🎞 Uniendo clips en video final...")
            self.actualizar_estado("Uniendo video final", 0.8)

            with open(ARCHIVO_LISTA, "w", encoding="utf-8") as f:
                for ruta in normalizados:
                    f.write(f"file '{os.path.abspath(ruta)}'\n")

            comando_union = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ARCHIVO_LISTA,
                "-c", "copy", SALIDA
            ]
            
            subprocess.run(
                comando_union,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.log_mensaje(f"✅ Video creado exitosamente: {SALIDA}")
            self.actualizar_estado("Limpiando archivos temporales", 0.95)
            self.limpiar_temporales()
            
            self.actualizar_estado("✅ Completado", 1.0)
            self.log_mensaje("🎉 ¡Proceso completado con éxito!")
            
        except Exception as e:
            self.log_mensaje(f"❌ Error inesperado: {e}")
            self.actualizar_estado("Error", 0)
        finally:
            self.finalizar_proceso()

    # --- FUNCIONES INTERNAS ---
    def descargar_clip(self, i, enlace):
        ruta_salida = os.path.join(CARPETA_DESCARGAS, f"clip_{i}.mp4")
        
        ejecutable_yt = "./yt-dlp"
        ejecutable_ffmpeg = shutil.which("ffmpeg")
        
        comando = [
            ejecutable_yt,
            "--ffmpeg-location", ejecutable_ffmpeg,
            "-f", f"bestvideo[height<={RESOLUCION_MAX}]+bestaudio/best[height<={RESOLUCION_MAX}]",
            "--merge-output-format", "mp4",
            "-o", ruta_salida,
            enlace
        ]
        
        try:
            subprocess.run(
                comando,
                check=True,
                capture_output=True,
                text=True
            )
            self.log_mensaje(f"  ✓ Clip {i} descargado")
            return i, ruta_salida
        except subprocess.CalledProcessError as e:
            self.log_mensaje(f"  ✗ Error en clip {i}: {e.stderr[:100]}")
            return i, None

    def normalizar_clip(self, i, ruta_entrada):
        ruta_salida = os.path.join(CARPETA_NORMALIZADOS, f"clip_norm_{i}.mp4")
        
        comando = [
            "ffmpeg",
            "-y", "-i", ruta_entrada,
            "-vf", f"scale=-2:{RESOLUCION_MAX},fps={FRAMERATE}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", ruta_salida
        ]
        
        try:
            subprocess.run(
                comando,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log_mensaje(f"  ✓ Clip {i} normalizado")
            return i, ruta_salida
        except:
            self.log_mensaje(f"  ✗ Error normalizando clip {i}")
            return i, None
    
    def limpiar_temporales(self):
        """Borra las carpetas y archivos intermedios."""
        self.log_mensaje("🧹 Limpiando archivos temporales...")
        
        carpetas_a_borrar = [CARPETA_DESCARGAS, CARPETA_NORMALIZADOS, "yt_cache"]
        archivos_a_borrar = [ARCHIVO_LISTA]

        for carpeta in carpetas_a_borrar:
            if os.path.exists(carpeta):
                try:
                    shutil.rmtree(carpeta)
                except Exception as e:
                    self.log_mensaje(f"  ⚠ No se pudo borrar {carpeta}: {e}")

        for archivo in archivos_a_borrar:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                except Exception as e:
                    self.log_mensaje(f"  ⚠ No se pudo borrar {archivo}: {e}")
        
        self.log_mensaje("✨ Limpieza completada")

if __name__ == "__main__":
    app = VideoApp()
    app.mainloop()