import os
import time
import wave
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from src.ports.inbound.audio_listener_port import AudioListenerPort

class MicrophoneAdapter(AudioListenerPort):
    def __init__(self, wake_word: str):
        self.wake_word = wake_word.lower()
        self.samplerate = 16000
        self.channels = 1
        self.ambient_threshold = 35.0
        
        print("[MIC] Dispositivos de audio disponiveis:")
        print(sd.query_devices())
        print(f"[MIC] Dispositivo padrao: {sd.default.device[0]}")
        
        # ===== Fase 1.1: Calibracao multi-amostra (3 x 1s) =====
        try:
            print("[MIC] Calibrando microfone (fique em silencio 3s)...")
            samples = []
            for i in range(3):
                chunk = sd.rec(int(1.0 * self.samplerate), samplerate=self.samplerate, 
                              channels=self.channels, dtype='float32')
                sd.wait()
                vol = np.linalg.norm(chunk) * 10
                samples.append(vol)
            
            mean = np.mean(samples)
            std = np.std(samples)
            # Threshold = media + 1.5 desvios padrao, minimo 30.0
            self.ambient_threshold = max(30.0, mean + 1.5 * std + 5.0)
            print(f"[MIC] Calibracao: ambiente={mean:.1f}, desvio={std:.1f}, limite={self.ambient_threshold:.1f}")
        except Exception as e:
            self.ambient_threshold = 45.0
            print(f"[MIC] Falha na calibracao, usando padrao ({self.ambient_threshold}): {e}")

        print("[MIC] Carregando modelo Faster Whisper (offline)...")
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        print("[MIC] Faster Whisper carregado!")

    # ===== Gravacao com threshold dinamico =====
    def _record_audio(self, timeout=5, max_duration=10, silence_duration=2.0) -> str:
        chunk_samples = int(self.samplerate * 0.1)
        audio_data = []
        # Captura 0.5s de pre-buffer para nao perder o inicio da fala
        pre_buffer = []
        pre_buffer_size = 5  # 5 chunks de 100ms = 500ms
        found_speech = False
        silence_start = None
        start_time = time.time()
        
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32') as stream:
                while True:
                    elapsed = time.time() - start_time
                    data, _ = stream.read(chunk_samples)
                    volume = np.linalg.norm(data) * 10
                    
                    if volume > self.ambient_threshold:
                        if not found_speech:
                            print(f"[MIC] Fala detectada! (vol={volume:.1f} > lim={self.ambient_threshold:.1f})")
                            # Inclui pre-buffer para nao perder o inicio
                            audio_data.extend(pre_buffer)
                        found_speech = True
                        silence_start = None
                        audio_data.append(data.copy())
                    elif found_speech:
                        audio_data.append(data.copy())
                        if silence_start is None:
                            silence_start = time.time()
                        elif (time.time() - silence_start) > silence_duration:
                            print("[MIC] Silencio detectado, finalizando.")
                            break
                    else:
                        # Pre-buffer rotativo (mantem ultimos 500ms)
                        pre_buffer.append(data.copy())
                        if len(pre_buffer) > pre_buffer_size:
                            pre_buffer.pop(0)
                    
                    if not found_speech and elapsed > timeout:
                        return None
                    if elapsed > max_duration:
                        print("[MIC] Tempo maximo atingido.")
                        break
        except Exception as e:
            print(f"[MIC] Erro na gravacao: {e}")
            return None
            
        if not audio_data:
            return None
        
        temp_file = "temp_mic.wav"
        recording = np.concatenate(audio_data, axis=0)
        duration = len(recording) / self.samplerate
        print(f"[MIC] Audio gravado: {duration:.1f}s")
        
        # Boost de volume para o Whisper ouvir melhor
        recording_boosted = np.clip(recording * 1.5, -1.0, 1.0)
        recording_int16 = (recording_boosted * 32767).astype(np.int16)
        
        with wave.open(temp_file, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(recording_int16.tobytes())
        return temp_file

    # ===== Transcrição =====
    def _transcribe(self, temp_file: str) -> str:
        if not temp_file or not os.path.exists(temp_file):
            return ""
        try:
            segments, _ = self.model.transcribe(temp_file, language="pt")
            text = " ".join([s.text for s in segments]).strip()
            if text:
                print(f"[MIC] Transcricao: '{text}'")
            return text
        except Exception as e:
            print(f"[MIC] Erro na transcricao: {e}")
            return ""
        finally:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    # ===== Fase 1.3: Fuzzy matching multi-wake-word =====
    def _matches_wake_word(self, text: str) -> bool:
        if not text:
            return False
        text = text.lower().strip()
        text = text.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        
        variations_map = {
            "jarvis": ["jarvis", "javis", "javits", "jarves", "davis", "davies", 
                       "ah vi", "ja vi", "já vi", "jarvi", "javi", "já vis"],
            "computador": ["computador", "computado", "computa", "comput", 
                          "computadores", "compute", "computer"]
        }
        
        variations = variations_map.get(self.wake_word, [self.wake_word])
        return any(v in text for v in variations)

    # ===== Fase 2: Detecção de palmas com RMS e anti-eco =====
    def _detect_claps(self, audio_data: np.ndarray) -> bool:
        clap_threshold = float(os.getenv("CLAP_THRESHOLD", "0.25"))
        clap_min_interval = float(os.getenv("CLAP_MIN_INTERVAL", "0.15"))
        
        # Calcula energia RMS em janelas de 20ms (mais robusto que pico)
        window_size = int(self.samplerate * 0.02)  # 20ms
        rms_values = []
        for i in range(0, len(audio_data) - window_size, window_size):
            window = audio_data[i:i + window_size]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)
        
        rms_values = np.array(rms_values)
        if len(rms_values) == 0:
            return False
        
        # Encontra janelas acima do threshold
        clap_windows = np.where(rms_values > clap_threshold)[0]
        if len(clap_windows) < 2:
            return False
        
        # Agrupa janelas consecutivas em eventos de palma
        clap_events = [clap_windows[0]]
        echo_reject_windows = int(0.05 / 0.02)  # 50ms de rejeicao de eco = ~2.5 janelas
        
        for i in range(1, len(clap_windows)):
            gap = clap_windows[i] - clap_windows[i-1]
            if gap > echo_reject_windows:  # Novo evento (não é eco)
                clap_events.append(clap_windows[i])
        
        # Verifica se temos >= 2 palmas com intervalo correto
        if len(clap_events) >= 2:
            for i in range(1, len(clap_events)):
                interval = (clap_events[i] - clap_events[i-1]) * 0.02  # Converte janelas para segundos
                if clap_min_interval < interval < 0.8:
                    print(f"[MIC] >> Palmas detectadas! (intervalo={interval:.2f}s)")
                    return True
        return False

    # ===== Wake Word Listener (Voz + Palmas) =====
    def listen_for_wake_word(self) -> bool:
        clap_enabled = os.getenv("CLAP_DETECTION_ENABLED", "true").lower() == "true"
        try:
            samples = int(self.samplerate * 2.0)
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32') as stream:
                data, _ = stream.read(samples)
                
                # 1. Palmas primeiro (rapido, sem transcrição)
                if clap_enabled and self._detect_claps(data):
                    return True
                
                # 2. Voz (transcricao via Whisper)
                temp_file = "temp_wake.wav"
                data_boosted = np.clip(data * 2.0, -1.0, 1.0)
                recording_int16 = (data_boosted * 32767).astype(np.int16)
                with wave.open(temp_file, "wb") as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.samplerate)
                    wf.writeframes(recording_int16.tobytes())
                
                text = self._transcribe(temp_file)
                if text and self._matches_wake_word(text):
                    print("[MIC] >>> Wake word detectada! <<<")
                    return True
            return False
        except Exception as e:
            print(f"[MIC] Erro no wake word: {e}")
            time.sleep(0.5)
            return False

    # ===== Command Listener =====
    def listen_for_command(self) -> str:
        print("[MIC] >> Escutando comando...")
        try:
            silence_dur = float(os.getenv("MIC_SILENCE_DURATION", "2.5"))
            max_dur = float(os.getenv("MIC_MAX_COMMAND_DURATION", "20"))
            temp_file = self._record_audio(timeout=10, max_duration=max_dur, silence_duration=silence_dur)
            if not temp_file:
                return ""
            text = self._transcribe(temp_file)
            if text:
                print(f"[MIC] Comando recebido: '{text}'")
            return text
        except Exception as e:
            print(f"[MIC] Erro no comando: {e}")
            return ""
