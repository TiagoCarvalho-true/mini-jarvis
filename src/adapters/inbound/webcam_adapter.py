import cv2
import os
import threading
import time
from typing import List, Optional
from src.ports.inbound.vision_port import VisionPort

class WebcamAdapter(VisionPort):
    def __init__(self, source=0, mode="on_demand", faces_dir="known_faces"):
        try:
            self.source = int(source)
        except:
            self.source = source
            
        self.mode = mode
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_detected_user: Optional[str] = None
        self._camera_available = True
        
        # Carrega o classificador Haar Cascade com protecao
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                print("[VISION] AVISO: Haar Cascade vazio, visao desativada.")
                self._camera_available = False
            else:
                print("[VISION] Haar Cascade carregado com sucesso.")
        except Exception as e:
            print(f"[VISION] Erro ao carregar Haar Cascade: {e}")
            self._camera_available = False
            self.face_cascade = None

        if self.mode == "continuous" and self._camera_available:
            self.start()

    def start(self):
        if self.mode == "continuous" and not self.running and self._camera_available:
            self.running = True
            self.thread = threading.Thread(target=self._continuous_loop, daemon=True)
            self.thread.start()
            print("[VISION] Modo continuo iniciado.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)

    def _continuous_loop(self):
        try:
            video_capture = cv2.VideoCapture(self.source)
            if not video_capture.isOpened():
                print("[VISION] Camera nao disponivel no modo continuo.")
                self._camera_available = False
                return
                
            while self.running:
                ret, frame = video_capture.read()
                if not ret:
                    time.sleep(1)
                    continue
                
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                    
                    # Fase 3.1: Invalida imediatamente quando nao ha rosto
                    if len(faces) > 0:
                        self.last_detected_user = "Senhor"
                    else:
                        self.last_detected_user = None
                except Exception as e:
                    print(f"[VISION] Erro no frame: {e}")
                
                time.sleep(1)
            video_capture.release()
        except Exception as e:
            print(f"[VISION] Erro fatal no loop continuo: {e}")
            self.running = False

    def check_once(self) -> Optional[str]:
        """Verifica presenca com protecao total contra falhas."""
        if not self._camera_available or not self.face_cascade:
            return None
            
        print("[VISION] Verificando presenca...")
        video_capture = None
        try:
            video_capture = cv2.VideoCapture(self.source)
            if not video_capture.isOpened():
                print("[VISION] Camera nao disponivel.")
                self._camera_available = False
                return None
            
            # Captura frames para estabilizar
            ret = False
            frame = None
            for _ in range(5):
                ret, frame = video_capture.read()
            
            if not ret or frame is None:
                return None
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                print(f"[VISION] Rosto detectado! ({len(faces)} pessoa(s))")
                self.last_detected_user = "Senhor"
                return "Senhor"
            
            # Fase 3.1: Invalida imediatamente
            self.last_detected_user = None
            return None
            
        except Exception as e:
            print(f"[VISION] Erro na deteccao: {e}")
            return None
        finally:
            if video_capture is not None:
                try:
                    video_capture.release()
                except:
                    pass

    def get_detected_user(self) -> Optional[str]:
        return self.last_detected_user

    def register_face(self, name: str, image_data: bytes) -> bool:
        print("[VISION] Registro de rostos desativado no modo OpenCV Puro.")
        return False

    def list_registered_faces(self) -> List[str]:
        return ["Senhor (Padrao)"]
