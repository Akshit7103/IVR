import json, os
from flask import Flask, render_template, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

# --- setup
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here-change-in-production")

# Get environment
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# Use environment variable for PUBLIC_URL in production
if FLASK_ENV == "production":
    PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PUBLIC_URL")
else:
    PUBLIC_URL = os.getenv("PUBLIC_URL")

DATA_PATH = "data/transactions.json"

def read_txns():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def write_txns(txns):
    with open(DATA_PATH, "w") as f:
        json.dump(txns, f, indent=2)

# Twilio client
twilio_client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TW_NUMBER = os.getenv("TWILIO_NUMBER")

# --- web pages
@app.get("/")
def index():
    return render_template("index.html", transactions=read_txns())

# --- APIs for UI
@app.get("/transactions")
def api_transactions():
    return jsonify(read_txns())

@app.post("/update_phone/<txn_id>")
def update_phone(txn_id):
    phone = (request.json or {}).get("client_phone", "")
    txns = read_txns()
    for t in txns:
        if t["id"] == txn_id:
            t["client_phone"] = phone
            break
    write_txns(txns)
    return jsonify({"ok": True})

@app.post("/set_action/<txn_id>")
def set_action(txn_id):
    action = (request.json or {}).get("action", "")
    txns = read_txns()
    for t in txns:
        if t["id"] == txn_id:
            t["action"] = action
            break
    write_txns(txns)
    return jsonify({"ok": True})

# --- start a call
@app.post("/call/<txn_id>")
def call(txn_id):
    txns = read_txns()
    txn = next((t for t in txns if t["id"] == txn_id), None)
    if not txn:
        return jsonify({"error": "not found"}), 404

    # mark connecting
    txn["action"] = "Connecting"
    write_txns(txns)

    twilio_client.calls.create(
        to=txn["client_phone"],
        from_=TW_NUMBER,
        url=f"{PUBLIC_URL}/voice/{txn_id}/step0",  # initial step: speak only, then redirect to listen
        status_callback=f"{PUBLIC_URL}/status/{txn_id}",
        status_callback_event=["completed", "no-answer", "busy", "failed"]
    )
    return jsonify({"ok": True})

# Helper function to convert amount to rupees and paise
def amount_to_words(amount):
    rupees = int(amount)
    paise = int((amount - rupees) * 100)
    if paise > 0:
        return f"{rupees} rupees and {paise} paise"
    return f"{rupees} rupees"

# ======================================================
# STEP 0: Initial confirmation — SPEAK, then LISTEN
# ======================================================

# --- Step 0: main explanation (no listening here)
@app.post("/voice/<txn_id>/step0")
def voice_step0(txn_id):
    txns = read_txns()
    txn = next((t for t in txns if t["id"] == txn_id), None)
    resp = VoiceResponse()

    if txn:
        amount_words = amount_to_words(txn['amount'])
        resp.say(
            f"Hello {txn['client_name']}, this is an automated call from your bank's security team. "
            f"We noticed a recent transaction at {txn['merchant_name']}, "
            f"for an amount of {amount_words}, "
            f"on {txn['transaction_date']}, made using your {txn['bank_name']} card "
            f"ending in {txn['card_number'][-4:]}. "
            "Could you please confirm if you authorized this transaction?"
        )
    else:
        resp.say("Hello. We have a security alert. Did you make the transaction?")

    # Ensure we never listen during this speech
    resp.pause(length=1)

    # Now move to the listening step with retry counter
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step0/listen?retry=0")
    return str(resp)

# --- Step 0 listen: Gather only (no long speech)
@app.post("/voice/<txn_id>/step0/listen")
def voice_step0_listen(txn_id):
    retry = int(request.args.get("retry", 0))
    resp = VoiceResponse()

    g = Gather(
        input="speech",
        action=f"/voice/{txn_id}/step0/response?retry={retry}",
        method="POST",
        timeout=5,
        language="en-IN",
        speechTimeout="auto",
        bargeIn=False,
        hints="yes,no"
    )
    # No long explanation here; we are just listening.
    resp.append(g)

    # If no input, Twilio will execute the code below after timeout.
    if retry >= 2:
        resp.say("We did not receive your answer. Goodbye.")
        resp.hangup()
    else:
        resp.say("We did not receive that. Please answer after the beep.")
        resp.pause(length=1)
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step0/listen?retry={retry + 1}")

    return str(resp)

@app.post("/voice/<txn_id>/step0/response")
def voice_step0_response(txn_id):
    retry = int(request.args.get('retry', 0))
    speech = (request.form.get("SpeechResult", "") or "").strip().lower()
    print(f"[STEP0] Speech detected: '{speech}' (retry: {retry})")
    print(f"[STEP0] Full form data: {dict(request.form)}")
    resp = VoiceResponse()

    # Check for valid yes response
    if any(word in speech for word in ["yes", "yeah", "yep", "correct", "true"]):
        # Customer confirmed - end call
        txns = read_txns()
        for t in txns:
            if t["id"] == txn_id:
                t["action"] = "Resolved"
                break
        write_txns(txns)

        resp.say("Thank you for confirming. No further action is required. Have a great day!")
        resp.hangup()

    # Check for valid no response
    elif any(word in speech for word in ["no", "nope", "nah", "not", "never"]):
        # Customer denied - go to step 1
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step1")

    else:
        # Unclear response or empty - go back to listen
        resp.say("Sorry, I did not catch that.")
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step0/listen?retry={retry + 1}")

    return str(resp)

# ======================================================
# STEP 1: Card details shared?
# ======================================================

# --- Step 1: speak question only
@app.post("/voice/<txn_id>/step1")
def voice_step1(txn_id):
    resp = VoiceResponse()
    resp.say("Have you shared your card details with anyone recently?")
    resp.pause(length=1)
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step1/listen?retry=0")
    return str(resp)

# --- Step 1 listen: Gather only
@app.post("/voice/<txn_id>/step1/listen")
def voice_step1_listen(txn_id):
    retry = int(request.args.get("retry", 0))
    resp = VoiceResponse()

    g = Gather(
        input="speech",
        action=f"/voice/{txn_id}/step1/response?retry={retry}",
        method="POST",
        timeout=5,
        language="en-IN",
        speechTimeout="auto",
        bargeIn=False,
        hints="yes,no"
    )
    resp.append(g)

    if retry >= 2:
        resp.say("We did not receive your answer. Goodbye.")
        resp.hangup()
    else:
        resp.say("We did not receive that. Please answer after the beep.")
        resp.pause(length=1)
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step1/listen?retry={retry + 1}")

    return str(resp)

@app.post("/voice/<txn_id>/step1/response")
def voice_step1_response(txn_id):
    retry = int(request.args.get('retry', 0))
    speech = (request.form.get("SpeechResult", "") or "").strip().lower()
    print(f"[STEP1] Speech detected: '{speech}' (retry: {retry})")
    resp = VoiceResponse()

    # Check if valid response (yes or no)
    if any(word in speech for word in ["yes", "yeah", "yep", "no", "nope", "nah", "not"]):
        # Both yes/no go to step 2
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step2")
    else:
        # Unclear response - go back to listen
        resp.say("Sorry, I did not catch that.")
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step1/listen?retry={retry + 1}")

    return str(resp)

# ======================================================
# STEP 2: Other suspicious transactions?
# ======================================================

# --- Step 2: speak question only
@app.post("/voice/<txn_id>/step2")
def voice_step2(txn_id):
    resp = VoiceResponse()
    resp.say("Have you noticed any other suspicious transactions in your account?")
    resp.pause(length=1)
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step2/listen?retry=0")
    return str(resp)

# --- Step 2 listen: Gather only
@app.post("/voice/<txn_id>/step2/listen")
def voice_step2_listen(txn_id):
    retry = int(request.args.get("retry", 0))
    resp = VoiceResponse()

    g = Gather(
        input="speech",
        action=f"/voice/{txn_id}/step2/response?retry={retry}",
        method="POST",
        timeout=5,
        language="en-IN",
        speechTimeout="auto",
        bargeIn=False,
        hints="yes,no"
    )
    resp.append(g)

    if retry >= 2:
        resp.say("We did not receive your answer. Goodbye.")
        resp.hangup()
    else:
        resp.say("We did not receive that. Please answer after the beep.")
        resp.pause(length=1)
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step2/listen?retry={retry + 1}")

    return str(resp)

@app.post("/voice/<txn_id>/step2/response")
def voice_step2_response(txn_id):
    retry = int(request.args.get('retry', 0))
    speech = (request.form.get("SpeechResult", "") or "").strip().lower()
    print(f"[STEP2] Speech detected: '{speech}' (retry: {retry})")
    resp = VoiceResponse()

    # Check if valid response (yes or no)
    if any(word in speech for word in ["yes", "yeah", "yep", "no", "nope", "nah", "not"]):
        # Both yes/no go to step 3
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step3")
    else:
        # Unclear response - go back to listen
        resp.say("Sorry, I did not catch that.")
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step2/listen?retry={retry + 1}")

    return str(resp)

# ======================================================
# STEP 3: Inform about next steps (no gather)
# ======================================================

@app.post("/voice/<txn_id>/step3")
def voice_step3(txn_id):
    resp = VoiceResponse()
    resp.say(
        "Thank you for the information. We will block this transaction and issue a new card for your safety."
    )
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step4")
    return str(resp)

# ======================================================
# STEP 4: Card delivery preference — SPEAK, then LISTEN
# ======================================================

# --- Step 4: speak question only
@app.post("/voice/<txn_id>/step4")
def voice_step4(txn_id):
    resp = VoiceResponse()
    resp.say(
        "Would you like to receive a physical card by mail, or a virtual card for immediate use?"
    )
    resp.pause(length=1)
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step4/listen?retry=0")
    return str(resp)

# --- Step 4 listen: Gather only
@app.post("/voice/<txn_id>/step4/listen")
def voice_step4_listen(txn_id):
    retry = int(request.args.get("retry", 0))
    resp = VoiceResponse()

    g = Gather(
        input="speech",
        action=f"/voice/{txn_id}/step4/response?retry={retry}",
        method="POST",
        timeout=5,
        language="en-IN",
        speechTimeout="auto",
        bargeIn=False,
        hints="physical,virtual"
    )
    resp.append(g)

    if retry >= 2:
        resp.say("We did not receive your answer. Goodbye.")
        resp.hangup()
    else:
        resp.say("We did not receive that. Please say physical or virtual after the beep.")
        resp.pause(length=1)
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step4/listen?retry={retry + 1}")

    return str(resp)

@app.post("/voice/<txn_id>/step4/response")
def voice_step4_response(txn_id):
    retry = int(request.args.get('retry', 0))
    speech = (request.form.get("SpeechResult", "") or "").strip().lower()
    print(f"[STEP4] Speech detected: '{speech}' (retry: {retry})")
    resp = VoiceResponse()

    if "physical" in speech:
        # Physical card flow - steps 5, 6, 7
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step5")
    elif "virtual" in speech:
        # Virtual only - step 8
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step8")
    else:
        # Unclear response - go back to listen
        resp.say("Sorry, I did not catch that.")
        resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step4/listen?retry={retry + 1}")

    return str(resp)

# ======================================================
# STEP 5: Physical card delivery (no gather)
# ======================================================

@app.post("/voice/<txn_id>/step5")
def voice_step5(txn_id):
    resp = VoiceResponse()
    resp.say("Your new physical card will arrive within 3 to 5 business days.")
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step6")
    return str(resp)

# ======================================================
# STEP 6: Virtual card issuance (with physical) (no gather)
# ======================================================

@app.post("/voice/<txn_id>/step6")
def voice_step6(txn_id):
    resp = VoiceResponse()
    resp.say("Meanwhile, a virtual card has been issued through your mobile banking app.")
    resp.redirect(f"{PUBLIC_URL}/voice/{txn_id}/step7")
    return str(resp)

# ======================================================
# STEP 7: Fraud case confirmation (physical path) (no gather)
# ======================================================

@app.post("/voice/<txn_id>/step7")
def voice_step7(txn_id):
    txns = read_txns()
    for t in txns:
        if t["id"] == txn_id:
            t["action"] = "Resolved"
            break
    write_txns(txns)

    resp = VoiceResponse()
    resp.say(
        "Also, a fraud case has been logged for this transaction. "
        "Thank you for your time, and rest assured your account is secure. Goodbye."
    )
    resp.hangup()
    return str(resp)

# ======================================================
# STEP 8: Virtual card only (no gather)
# ======================================================

@app.post("/voice/<txn_id>/step8")
def voice_step8(txn_id):
    txns = read_txns()
    for t in txns:
        if t["id"] == txn_id:
            t["action"] = "Resolved"
            break
    write_txns(txns)

    resp = VoiceResponse()
    resp.say(
        "A virtual card has been issued through your mobile banking app for immediate use. "
        "A fraud case has been logged for this transaction. "
        "Thank you for your cooperation, and your account is secure. Goodbye."
    )
    resp.hangup()
    return str(resp)

# ======================================================
# STATUS CALLBACK (no change to logic)
# ======================================================

@app.post("/status/<txn_id>")
def status(txn_id):
    call_status = request.form.get("CallStatus", "")
    print(f"[STATUS] Transaction {txn_id} - Call status: {call_status}")

    if call_status in ["no-answer", "busy"]:
        update(txn_id, "Not Answered")
    elif call_status in ["failed"]:
        update(txn_id, "Disconnected")
    elif call_status in ["completed"]:
        # Check if it was resolved or marked as fraud already
        txns = read_txns()
        txn = next((t for t in txns if t["id"] == txn_id), None)
        if txn and txn["action"] not in ["Resolved", "Mark As Fraud"]:
            # If not explicitly set, mark as disconnected
            update(txn_id, "Disconnected")

    return ("", 204)

def update(txn_id, action):
    txns = read_txns()
    for t in txns:
        if t["id"] == txn_id:
            t["action"] = action
            break
    write_txns(txns)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
