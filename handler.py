import base64
import runpod
import requests

KOKORO_URL = "http://localhost:8880"
SUPPORTED_FORMATS = {"mp3", "wav", "flac", "opus", "aac", "pcm"}


def call_kokoro(endpoint, method="POST", data=None, timeout=30):
    url = f"{KOKORO_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)

        response.raise_for_status()
        return response.json() if response.text else {}

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError("Não foi possível conectar ao servidor Kokoro interno") from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError("Timeout ao chamar o servidor Kokoro") from e
    except requests.exceptions.RequestException as e:
        response_text = ""
        try:
            response_text = e.response.text[:500] if e.response is not None and e.response.text else ""
        except Exception:
            response_text = ""
        raise RuntimeError(f"Erro HTTP na API Kokoro: {response_text or str(e)}") from e


def estimate_duration_seconds(audio_base64):
    try:
        audio_bytes = base64.b64decode(audio_base64)
        return round(len(audio_bytes) / 48000, 2)
    except Exception:
        return None


def validate_text(value):
    return isinstance(value, str) and value.strip() != ""


def validate_format(output_format):
    return output_format in SUPPORTED_FORMATS


def handler(job):
    job_input = job.get("input", {})

    text = job_input.get("text", "")
    if not validate_text(text):
        return {
            "status": "error",
            "error": "Parâmetro 'text' é obrigatório e deve ser uma string não vazia"
        }

    voice = job_input.get("voice")
    if not voice or not isinstance(voice, str):
        return {
            "status": "error",
            "error": "Parâmetro 'voice' é obrigatório. Envie uma voz válida.",
            "available_voices_endpoint": "Use 'type': 'list_voices' para ver vozes disponíveis"
        }

    try:
        speed = float(job_input.get("speed", 1.0))
    except (TypeError, ValueError):
        return {
            "status": "error",
            "error": "Parâmetro 'speed' deve ser numérico"
        }

    output_format = str(job_input.get("format", "mp3")).lower()
    if not validate_format(output_format):
        return {
            "status": "error",
            "error": f"Formato '{output_format}' não suportado. Use: mp3, wav, flac, opus, aac, pcm"
        }

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
            "status": "error",
            "error": "Resposta inválida do servidor Kokoro",
            "kokoro_response": response
        }

    audio_base64 = response["audio"]
    duration_approx = estimate_duration_seconds(audio_base64)

    return {
        "status": "success",
        "audio_base64": audio_base64,
        "format": output_format,
        "duration_seconds": duration_approx,
        "sample_rate": 24000,
        "voice": voice,
        "text_preview": text[:100] + ("..." if len(text) > 100 else "")
    }


def list_voices_handler(job):
    response = call_kokoro("/v1/voices", "GET", timeout=15)

    voices = []
    if "voices" in response and isinstance(response["voices"], list):
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


def combine_voices_handler(job):
    job_input = job.get("input", {})

    text = job_input.get("text", "")
    if not validate_text(text):
        return {
            "status": "error",
            "error": "Parâmetro 'text' é obrigatório e deve ser uma string não vazia"
        }

    voices = job_input.get("voices", [])
    weights = job_input.get("weights", [])

    if not isinstance(voices, list) or not isinstance(weights, list) or not voices:
        return {
            "status": "error",
            "error": "Parâmetros 'voices' e 'weights' devem ser listas não vazias"
        }

    if len(voices) != len(weights):
        return {
            "status": "error",
            "error": "voices e weights devem ter o mesmo tamanho"
        }

    try:
        normalized_weights = [float(w) for w in weights]
    except (TypeError, ValueError):
        return {
            "status": "error",
            "error": "Todos os valores de 'weights' devem ser numéricos"
        }

    voice_combination = "+".join(
        [f"{v}({w:g})" for v, w in zip(voices, normalized_weights)]
    )

    try:
        speed = float(job_input.get("speed", 1.0))
    except (TypeError, ValueError):
        return {
            "status": "error",
            "error": "Parâmetro 'speed' deve ser numérico"
        }

    output_format = str(job_input.get("format", "mp3")).lower()
    if not validate_format(output_format):
        return {
            "status": "error",
            "error": f"Formato '{output_format}' não suportado. Use: mp3, wav, flac, opus, aac, pcm"
        }

    kokoro_data = {
        "model": "kokoro",
        "input": text,
        "voice": voice_combination,
        "speed": speed,
        "response_format": output_format
    }

    response = call_kokoro("/v1/audio/speech", "POST", kokoro_data)

    if "audio" not in response:
        return {
            "status": "error",
            "error": "Resposta inválida do servidor Kokoro",
            "kokoro_response": response
        }

    audio_base64 = response["audio"]
    duration_approx = estimate_duration_seconds(audio_base64)

    return {
        "status": "success",
        "audio_base64": audio_base64,
        "format": output_format,
        "duration_seconds": duration_approx,
        "voice_combination": voice_combination,
        "sample_rate": 24000
    }


def route_handler(job):
    job_input = job.get("input", {})
    event_type = job_input.get("type", "generate")

    if event_type == "list_voices":
        return list_voices_handler(job)
    if event_type == "combine_voices":
        return combine_voices_handler(job)

    return handler(job)


if __name__ == "__main__":
    runpod.serverless.start({"handler": route_handler})
