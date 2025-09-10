from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Get Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing. Please set it in your .env file.")

# ✅ Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Use Gemini 2.0 Flash model
model = genai.GenerativeModel("gemini-2.0-flash")

# ✅ Hardcoded FAQs (backup answers)
faqs = {
    "courses": "RCPIT offers B.Tech, M.Tech, and Ph.D. programs in various streams.",
    "fees": "The annual fees for Computer Engineering is approx ₹95,000.",
    "hostel": "Yes, RCPIT provides hostel facilities for both boys and girls.",
    "placement": "The Training & Placement Cell at RCPIT has tie-ups with leading companies."
}

def ask_gemini(prompt: str) -> str:
    """Wrapper for Gemini with error handling"""
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            return None
    except Exception as e:
        print("Gemini Error:", e)  # Debug log
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_question = data.get("question", "").lower()

    faq_answer = None
    for keyword, answer in faqs.items():
        if keyword in user_question:
            faq_answer = answer
            break

    # ✅ Always force Gemini if "rcpit" is mentioned
    if "rcpit" in user_question:
        prompt = f"""
        You are the official chatbot for RCPIT (R.C. Patel Institute of Technology).
        The user mentioned 'RCPIT', so you must answer clearly in 2–3 sentences.

        Question: {user_question}
        """
        gemini_answer = ask_gemini(prompt)
        return jsonify({"answer": gemini_answer or faq_answer or "Sorry, I couldn’t get an answer right now."})

    # ✅ Otherwise hybrid logic (FAQ + Gemini)
    prompt = f"""
    You are the official chatbot for RCPIT (R.C. Patel Institute of Technology).
    Provide accurate and student-friendly answers in 2–3 sentences.

    FAQ Answer (if any): {faq_answer}
    User Question: {user_question}

    Rules:
    - If FAQ answer exists but you can improve it, provide your improved version.
    - If no FAQ, generate the best possible RCPIT-related answer.
    - If unrelated, reply only: "I can only answer RCPIT-related queries."
    """
    gemini_answer = ask_gemini(prompt)

    if gemini_answer and gemini_answer.lower() != (faq_answer or "").lower():
        return jsonify({"answer": gemini_answer})
    elif faq_answer:
        return jsonify({"answer": faq_answer})
    else:
        return jsonify({"answer": gemini_answer or "Sorry, I couldn’t get an answer right now."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
