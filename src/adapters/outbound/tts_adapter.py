import numpy as np
try:
    import sounddevice as sd
    from piper.voice import PiperVoice
except ImportError as e:
    print(f"[TTS] Erro ao importar dependencias: {e}")
from src.ports.outbound.tts_port import TTSPort

class TTSAdapter(TTSPort):
    def __init__(self):
        self.model_path = "pt_BR-faber-medium.onnx"
        self.voice = None
        self.sample_rate = 22050

        print(f"[TTS] Dispositivo de saida padrao: {sd.default.device[1]}")
        
        if __import__('os').path.exists(self.model_path):
            try:
                print("[TTS] Carregando voz do Piper...")
                self.voice = PiperVoice.load(self.model_path)
                self.sample_rate = self.voice.config.sample_rate
                print(f"[TTS] Voz carregada! (Sample rate: {self.sample_rate}Hz)")
            except Exception as e:
                print(f"[TTS] Erro ao carregar voz: {e}")
        else:
            print(f"[TTS] AVISO: Modelo '{self.model_path}' nao encontrado!")

    def speak(self, text: str) -> None:
        print(f"J.A.R.V.I.S: {text}")
        
        if not self.voice:
            print("[TTS OFF] Modelo nao carregado.")
            return
        
        try:
            # synthesize() retorna um generator de AudioChunk com audio_float_array
            audio_chunks = []
            for chunk in self.voice.synthesize(text):
                audio_chunks.append(chunk.audio_float_array)
            
            if not audio_chunks:
                print("[TTS] Nenhum audio gerado.")
                return
            
            # Junta todos os chunks em um unico array
            audio_data = np.concatenate(audio_chunks)
            
            # Garante que esta no range [-1.0, 1.0]
            audio_data = np.clip(audio_data, -1.0, 1.0)
            
            duration = len(audio_data) / self.sample_rate
            print(f"[TTS] Reproduzindo ({duration:.1f}s)...")
            sd.play(audio_data, self.sample_rate)
            sd.wait()
            print("[TTS] Audio finalizado.")
            
        except Exception as e:
            print(f"[TTS] Erro na sintese: {e}")
            import traceback
            traceback.print_exc()
