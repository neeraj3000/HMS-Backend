from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile, os, time
import httpx
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI Utilities"])

ASSEMBLY_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

if not ASSEMBLY_KEY:
    raise Exception("Missing ASSEMBLYAI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("Missing GEMINI_API_KEY")


@router.post("/transcribe-summarize")
async def transcribe_and_summarize(file: UploadFile = File(...)):
    try:
        # -----------------------
        # 1. Save File
        # -----------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            audio_path = tmp.name

        # -----------------------
        # 2. Upload to AssemblyAI
        # -----------------------
        with open(audio_path, "rb") as audio:
            upload_res = httpx.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLY_KEY},
                content=audio
            )

        if upload_res.status_code != 200:
            raise HTTPException(500, "Upload failed")

        audio_url = upload_res.json()["upload_url"]

        # -----------------------
        # 3. Request transcription ONLY
        # -----------------------
        task = httpx.post(
            "https://api.assemblyai.com/v2/transcript",
            json={"audio_url": audio_url, "language_detection": True},
            headers={"authorization": ASSEMBLY_KEY}
        )

        if task.status_code != 200:
            raise HTTPException(500, "Transcription start failed")

        transcript_id = task.json()["id"]

        # -----------------------
        # 4. Poll until done
        # -----------------------
        while True:
            poll = httpx.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": ASSEMBLY_KEY}
            ).json()

            if poll["status"] == "completed":
                break
            if poll["status"] == "error":
                raise HTTPException(500, poll["error"])

            time.sleep(1)

        transcribed_text = poll["text"]

        # -----------------------
        # 5. Summarize using Gemini
        # -----------------------
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        prompt = f"""
You are a medical communication assistant.

Rewrite the doctor’s dictation in simple language the patient can understand:

• What medicines to take  
• When to take them  
• Why they are needed (if clear from context)  
• Any precautions  

Avoid medical jargon.

Dictation:
{transcribed_text}

"""

        gemini_result = model.generate_content(prompt)
        summary = gemini_result.text.strip()

        # -----------------------
        # 6. Clean up + return
        # -----------------------
        os.remove(audio_path)

        return {
            "transcribed_text": transcribed_text,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(500, f"AI processing failed: {str(e)}")
