# AI Virtual Tutor

An AI-powered virtual tutor for real-time student doubt resolution.

## Features
- Text, Voice and Document input
- Talking avatar output (Ms. Aira)
- Chat history with SQLite database
- Explains AI concepts in simple English

## Tech Stack
- Frontend : HTML, CSS, JavaScript
- Backend  : Python, Flask
- AI Model : Groq API (Llama 3.3 70B)
- Image AI : Flux via Hugging Face Inference
- Database : SQLite
- Voice    : Web Speech API (browser)

## How to Run
1. Install dependencies  : pip install -r requirements.txt
2. Add GROQ_API_KEY in   : .env file
3. Add `HF_TOKEN` in     : `.env` file
4. Set `.env`            : `IMAGE_PROVIDER=flux`
5. Set Flux model        : `HF_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell`
6. Start the server      : python run.py
7. Open in Chrome        : http://localhost:5000

## Flux Note
- The tutor now generates images with Flux and renders them directly inside the same chat screen as the text response.
- The generated files are saved under `frontend/generated/`.
