import os
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from src.ports.inbound.audio_listener_port import AudioListenerPort

class MicrophoneAdapter(AudioListenerPort):
    def __init__(self, wake_word: str):
        self.wake_word = wake_word.lower()
        self.samplerate = 16000
        self.channels = 1
        
        # Mostra dispositivos de entrada disponíveis
        print("[MIC] Dispositivos de audio disponiveis:")
        print(sd.query_devices())
        print(f"[MIC] Dispositivo de entrada padrao: {sd.default.device[0]}")
        
        # Testa se o microfone funciona
        try:
            test = sd.rec(int(0.5 * self.samplerate), samplerate=self.samplerate, channels=self.channels, dtype='float32')
            sd.wait()
            volume = np.linalg.norm(test) * 10
            print(f"[MIC] Teste de microfone OK! Volume ambiente: {volume:.4f}")
        except Exception as e:
            print(f"[MIC] ERRO ao acessar microfone: {e}")
        
        print("[MIC] Carregando modelo Faster Whisper (offline)...")
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        print("[MIC] Faster Whisper carregado com sucesso!")

    def _record_audio(self, timeout=5, max_duration=10, silence_threshold=35.0, silence_duration=1.5) -> str:
        """
        Grava áudio do microfone até detectar silêncio após fala.
        Retorna o caminho do arquivo WAV temporário ou None.
        """
        import wave
        
        chunk_duration = 0.1  # 100ms por chunk
        chunk_samples = int(self.samplerate * chunk_duration)
        
        audio_data = []
        found_speech = False
        silence_start = None
        start_time = time.time()
        
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32') as stream:
                while True:
                    elapsed = time.time() - start_time
                    
                    # Lê um chunk do microfone
                    data, overflowed = stream.read(chunk_samples)
                    volume = np.linalg.norm(data) * 10
                    
                    # Detecta fala
                    if volume > silence_threshold:
                        if not found_speech:
                            print(f"[MIC] Fala detectada! (volume={volume:.4f})")
                        found_speech = True
                        silence_start = None
                        audio_data.append(data.copy())
                    elif found_speech:
                        audio_data.append(data.copy())
                        if silence_start is None:
                            silence_start = time.time()
                        elif (time.time() - silence_start) > silence_duration:
                            print("[MIC] Silencio detectado, finalizando gravacao.")
                            break
                    
                    # Timeout sem fala
                    if not found_speech and elapsed > timeout:
                        return None
                    
                    # Limite máximo de gravação
                    if elapsed > max_duration:
                        print("[MIC] Tempo maximo atingido.")
                        break
        except Exception as e:
            print(f"[MIC] Erro na gravacao: {e}")
            return None
                    
        if not audio_data:
            return None
            
        # Salva como WAV temporário
        temp_file = "temp_mic.wav"
        recording = np.concatenate(audio_data, axis=0)
        recording_int16 = (recording * 32768).astype(np.int16)
        
        with wave.open(temp_file, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(recording_int16.tobytes())
        
        duration = len(recording) / self.samplerate
        print(f"[MIC] Audio gravado: {duration:.1f}s")
        return temp_file

    def _transcribe(self, temp_file: str) -> str:
        if not temp_file or not os.path.exists(temp_file):
            return ""
            
        try:
            print("[MIC] Transcrevendo...")
            segments, info = self.model.transcribe(temp_file, language="pt")
            text = " ".join([segment.text for segment in segments])
            result = text.strip()
            print(f"[MIC] Transcricao: '{result}'")
            return result
        except Exception as e:
            print(f"[MIC] Erro na transcricao: {e}")
            return ""
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _matches_wake_word(self, text: str) -> bool:
        """Verifica se o texto contém a wake word ou variações próximas."""
        text = text.lower().strip()
        text = text.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        
        # Variações comuns que o Whisper transcreve
        wake_words = [
            "jarvis", "javis", "javits", "jarves", "jarvs",
            "jarvas", "jarvez", "jarvi", "javi", "jarves",
            "travis", "chaves", "chavis", "davies", "davis",
            "jarvís", "jarvês"
        ]
        
        for word in wake_words:
            if word in text:
                return True
        return False

    def listen_for_wake_word(self) -> bool:
        try:
            temp_file = self._record_audio(timeout=3, max_duration=5, silence_threshold=55.0, silence_duration=1.0)
            if not temp_file:
                return False
                
            text = self._transcribe(temp_file)
            
            if text and self._matches_wake_word(text):
                print(f"[MIC] >>> Wake word detectada! <<<")
                return True
            return False
        except Exception as e:
            print(f"[MIC] Erro no listen_for_wake_word: {e}")
            time.sleep(1)
            return False

    def listen_for_command(self) -> str:
        print("[MIC] >> Escutando comando...")
        try:
            temp_file = self._record_audio(timeout=8, max_duration=15, silence_duration=1.5)
            if not temp_file:
                return ""
            return self._transcribe(temp_file)
        except Exception as e:
            print(f"[MIC] Erro no listen_for_command: {e}")
            return ""
