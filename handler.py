import runpod
import requests
import base64

# ============================================
# CONFIGURAÇÕES
# ============================================
KOKORO_URL = "http://localhost:8880"

# ============================================
# FUNÇÃO AUXILIAR: CHAMA A API DO KOKORO
# ============================================
def call_kokoro(endpoint, method="POST", data=None):
    """Faz chamadas HTTP para o servidor Kokoro interno."""
    url = f"{KOKORO_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=30)

        response.raise_for_status()
        return response.json() if response.text else {}

    except requests.exceptions.ConnectionError:
        raise Exception("Não foi possível conectar ao servidor Kokoro interno")
    except requests.exceptions.Timeout:
        raise Exception("Timeout ao chamar o servidor Kokoro")
    except Exception as e:
        raise Exception(f"Erro na API Kokoro: {str(e)}")

# ============================================
# HANDLER PRINCIPAL DO RUNPOD
# ============================================
def handler(event):
    """
    Handler do RunPod Serverless.

    A VOZ VEM DO SEU CÓDIGO (input do usuário), não é pré-definida!

    Recebe: {
        "input": {
            "text": "Hello world!",
            "voice": "af_bella",
            "speed": 1.0,
            "format": "mp3"
        }
    }
    """
    try:
        input_data = event.get("input", {})

        # --- Extrai parâmetros ---
        text = input_data.get("text", "")
        if not text or not isinstance(text, str):
            return {
                "error": "Parâmetro 'text' é obrigatório e deve ser uma string",
                "status": "error"
            }

        # ============================================
        # A VOZ VEM DO SEU CÓDIGO! NÃO É PRÉ-DEFINIDA!
        # ============================================
        voice = input_data.get("voice")
        if not voice:
            return {
                "error": "Parâmetro 'voice' é obrigatório. Envie uma voz válida.",
                "status": "error",
                "available_voices_endpoint": "Use 'type': 'list_voices' para ver vozes disponíveis"
            }

        speed = float(input_data.get("speed", 1.0))
        output_format = input_data.get("format", "mp3").lower()

        # Valida formato
        if output_format not in ["mp3", "wav", "flac", "opus", "aac", "pcm"]:
            return {
                "error": f"Formato '{output_format}' não suportado. Use: mp3, wav, flac, opus, aac, pcm",
                "status": "error"
            }

        print(f"🎙️  Gerando áudio: voice={voice}, speed={speed}, format={output_format}")
        print(f"   Texto: '{text[:80]}...'")

        # ============================================
        # CHAMA A API DO KOKORO COM A VOZ DO USUÁRIO
        # ============================================
        kokoro_data = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": output_format
        }

        response = call_kokoro("/v1/audio/speech", "POST", kokoro_data)

        if "audio" not in response:
            return {
                "error": "Resposta inválida do servidor Kokoro",
                "status": "error",
                "kokoro_response": response
            }

        audio_base64 = response["audio"]

        # Calcula duração aproximada
        audio_bytes = base64.b64decode(audio_base64)
        duration_approx = len(audio_bytes) / 48000

        print(f"✅ Áudio gerado: ~{duration_approx:.2f}s, formato={output_format}")

        return {
            "status": "success",
            "audio_base64": audio_base64,
            "format": output_format,
            "duration_seconds": round(duration_approx, 2),
            "sample_rate": 24000,
            "voice": voice,
            "text_preview": text[:100] + ("..." if len(text) > 100 else "")
        }

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"❌ Erro: {error_msg}")
        print(traceback.format_exc())

        return {
            "status": "error",
            "error": error_msg,
            "error_type": type(e).__name__
        }

# ============================================
# HANDLER PARA LISTAR VOZES
# ============================================
def list_voices_handler(event):
    """Lista todas as vozes disponíveis no Kokoro."""
    try:
        response = call_kokoro("/v1/voices", "GET")

        voices = []
        if "voices" in response:
            for v in response["voices"]:
                voices.append({
                    "id": v.get("id", ""),
                    "name": v.get("name", ""),
                    "language": v.get("language", ""),
                    "gender": v.get("gender", "")
                })

        return {
            "status": "success",
            "voices": voices,
            "count": len(voices)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================
# HANDLER PARA COMBINAR VOZES (voice blending)
# ============================================
def combine_voices_handler(event):
    """
    Cria uma voz customizada combinando vozes existentes.

    Recebe: {
        "input": {
            "type": "combine_voices",
            "text": "Hello world!",
            "voices": ["af_bella", "af_sky"],
            "weights": [2, 1],
            "speed": 1.0,
            "format": "mp3"
        }
    }
    """
    try:
        input_data = event.get("input", {})

        text = input_data.get("text", "")
        if not text:
            return {"error": "text é obrigatório", "status": "error"}

        voices = input_data.get("voices", [])
        weights = input_data.get("weights", [])

        if len(voices) != len(weights):
            return {
                "error": "voices e weights devem ter o mesmo tamanho",
                "status": "error"
            }

        # Cria string de combinação: "af_bella(2)+af_sky(1)"
        voice_combination = "+".join([
            f"{v}({w})" for v, w in zip(voices, weights)
        ])

        speed = float(input_data.get("speed", 1.0))
        output_format = input_data.get("format", "mp3").lower()

        print(f"🎙️  Combinando vozes: {voice_combination}")
        print(f"   Texto: '{text[:80]}...'")

        kokoro_data = {
            "model": "kokoro",
            "input": text,
            "voice": voice_combination,
            "speed": speed,
            "response_format": output_format
        }

        response = call_kokoro("/v1/audio/speech", "POST", kokoro_data)

        audio_base64 = response["audio"]
        audio_bytes = base64.b64decode(audio_base64)
        duration_approx = len(audio_bytes) / 48000

        print(f"✅ Áudio combinado gerado: ~{duration_approx:.2f}s")

        return {
            "status": "success",
            "audio_base64": audio_base64,
            "format": output_format,
            "duration_seconds": round(duration_approx, 2),
            "voice_combination": voice_combination,
            "sample_rate": 24000
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================
# ROTEADOR DE HANDLERS
# ============================================
def route_handler(event):
    """Roteia para o handler correto baseado no tipo de evento."""
    input_data = event.get("input", {})
    event_type = input_data.get("type", "generate")

    if event_type == "list_voices":
        return list_voices_handler(event)
    elif event_type == "combine_voices":
        return combine_voices_handler(event)
    else:
        return handler(event)

# ============================================
# INICIA O SERVIDOR RUNPOD
# ============================================
if __name__ == "__main__":
    print("🚀 Iniciando RunPod Serverless Worker...")
    print("   Aguardando events...")
    print("   Use 'type': 'generate' (padrão), 'list_voices', ou 'combine_voices'")
    runpod.serverless.start({"handler": route_handler})
    except Exception as e:
        return {"error": f"❌ Erro: {str(e)}"}

# Inicia o RunPod serverless
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
