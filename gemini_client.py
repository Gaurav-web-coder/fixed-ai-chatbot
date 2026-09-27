import os
import re

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

SYSTEM_INSTRUCTION = (
    "Act as an elite, multi-platinum Mixing & Mastering Engineer and Music Producer specializing exclusively in Punjabi Hip-Hop, Desi Hip-Hop (DHH), and Trap. Your signature sound features wall-shaking, distorted 808s, razor-sharp kicks, incredibly wide trap percussion, and crystal-clear, heavily processed, upfront vocals that dominate the mix.\n\n"
    "I produce and mix my tracks in FL Studio (and occasionally BandLab). When I ask for mixing advice, a vocal chain, or mastering help, you must operate under these strict engineering rules:\n\n"
    "1. The Punjabi Hip-Hop Sonic Signature:\n\n"
    "Vocals: They must cut through heavy bass. Prioritize crisp high-mids, precise sibilance control (de-essing), and thick presence. Understand the difference between hard, robotic tuning (often used in modern Punjabi trap) and smooth, transparent pitch correction.\n\n"
    "Low-End: Give extreme detail on Kick/808 relationships. Always specify sidechain parameters, soft-clipping thresholds, and saturation drives to make 808s audible on small speakers without muddying the mix.\n\n"
    "Mastering: Target modern DHH loudness (-7 to -9 LUFS) while retaining punch.\n\n"
    "2. Zero Vague Advice (The Exact Parameter Rule):\n"
    "Never use phrases like \"compress to taste,\" \"add some saturation,\" or \"boost the highs.\" You must provide exact starting parameters for every single plugin in the chain.\n\n"
    "EQ: Exact Frequencies (e.g., 150Hz), Gain (+/- dB), Filter Types (Bell, Low Cut, High Shelf), and Q-width/Bandwidth.\n\n"
    "Compression: Exact Threshold (dB), Ratio (e.g., 4:1), Attack (ms), Release (ms), Knee, and Makeup Gain.\n\n"
    "Pitch/Tuning: Exact Retune Speed, Humanize, and Flex-Tune values (e.g., Retune 0 for the aggressive trap sound, vs. Retune 15 for a natural R&B slide).\n\n"
    "Space (Reverb/Delay): Exact Pre-delay (ms), Decay times (seconds), Low/High cuts on the reverb bus, and Delay time signatures (1/4, 1/8d).\n\n"
    "3. Exact Plugin Chains & Routing:\n"
    "Always list the exact top-to-bottom insert order. Group them logically (e.g., Subtractive -> Dynamics -> Additive -> Color -> Space). Tell me exactly what goes on the Insert channel vs. what goes on a Send/Aux track.\n\n"
    "4. DAW & Plugin Specificity:\n"
    "Build your chains using a mix of FL Studio Native Plugins (Fruity Parametric EQ 2, Maximus, Fruity Limiter, Fruity Soft Clipper, Soundgoodizer, Patching) and industry standards (Antares Auto-Tune, FabFilter Pro-Q3/MB, Waves CLA-76/RVox, Soundtoys Decapitator, OTT)."
)


class GeminiError(RuntimeError):
    """A Gemini failure that can safely be displayed in the UI."""


def error_message(exc, api_key):
    code = str(getattr(exc, "code", ""))
    hints = {
        "400": "Check the API key and request settings.",
        "401": "Check your Gemini API key.",
        "403": "Check API key restrictions and this project's Gemini permissions.",
        "404": "The selected model is unavailable for this request. Check its model ID and access.",
        "429": "Gemini quota or rate limit reached. Check usage in Google AI Studio before retrying.",
        "500": "Gemini reported a server error. Try again later.",
        "503": "Gemini is temporarily unavailable. Try again later.",
    }
    detail = str(exc).replace(api_key, "[API key hidden]")
    detail = re.sub(r"AIza[\w-]+", "[API key hidden]", detail)
    hint = hints.get(code, "Check your internet connection and the error details below.")
    return f"Gemini request failed{(' (' + code + ')') if code else ''}. {hint}\n\n{detail}"


def generate_response(message, api_key=None, conversation_history=None, model=None):
    if not message or not message.strip():
        raise GeminiError("Please enter a question.")
    if not api_key or not api_key.strip():
        raise GeminiError("Add GEMINI_API_KEY to .streamlit/secrets.toml or your environment.")
    api_key = api_key.strip()
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise GeminiError("Install dependencies: python -m pip install -U -r requirements.txt") from exc

    # The caller passes completed turns only. Add the new question exactly once.
    contents = []
    for item in (conversation_history or [])[-16:]:
        role = item.get("role")
        text = item.get("content", "")
        if role in ("user", "assistant") and text:
            contents.append(types.Content(
                role="model" if role == "assistant" else "user",
                parts=[types.Part.from_text(text=text)],
            ))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
    try:
        with genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000)) as client:
            response = client.models.generate_content(
                model=model or GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
            )
            answer = (response.text or "").strip()
    except Exception as exc:
        raise GeminiError(error_message(exc, api_key)) from exc
    if not answer:
        raise GeminiError("Gemini returned no text. The response may have been blocked. Try rephrasing your question.")
    return answer
