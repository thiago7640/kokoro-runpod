import runpod
import requests
import base64
import os

# URL interna do Kokoro (já roda na porta 8880 na imagem oficial)
KOKORO_URL = "http://localhost:8880/v1/audio/speech"

def handler(job):
    """
    Handler do RunPod que chama o Kokoro interno
    """
    job_input = job["input"]
    
    # Pega os parâmetros (mesmos nomes da API OpenAI do Kokoro)
    text = job_input.get("input", "")
    voice = job_input.get("voice", "af_bella")
    response_format = job_input.get("response_format", "mp3")
    speed = job_input.get("speed", 1.0)
    
    if not text:
        return {"error": "❌ 'input' (texto) é obrigatório!"}
    
    try:
        # Chama o Kokoro que já roda dentro do container
        response = requests.post(
            KOKORO_URL,
            json={
                "model": "kokoro",
                "input": text,
                "voice": voice,
                "response_format": response_format,
                "speed": speed
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "error": f"❌ Kokoro erro HTTP {response.status_code}",
                "details": response.text
            }
        
        # Converte o áudio MP3/WAV pra base64
        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        
        return {
            "status": "success",
            "audio_base64": audio_base64,
            "format": response_format,
            "voice": voice,
            "text": text,
            "size_bytes": len(response.content)
        }
        
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Kokoro não está rodando na porta 8880"}
    except Exception as e:
        return {"error": f"❌ Erro: {str(e)}"}

# Inicia o RunPod serverless
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
