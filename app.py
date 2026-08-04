import os
import time
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# ---- Settings (Railway par Variables mein set karo) ----
TOKEN           = os.environ.get("WHATSAPP_TOKEN", "")          # permanent access token
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "1090055494188737")  # Women Comforts
ACCESS_PIN      = os.environ.get("ACCESS_PIN", "1234")         # panel kholne ka PIN
GRAPH_VERSION   = "v21.0"


def send_template(to, tmpl, lang, var):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {"name": tmpl, "language": {"code": lang}},
    }
    if var:  # sirf tab jab template mein {{1}} variable ho
        payload["template"]["components"] = [
            {"type": "body", "parameters": [{"type": "text", "text": var}]}
        ]
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
    except Exception as e:
        return False, str(e)
    if r.status_code == 200:
        mid = data.get("messages", [{}])[0].get("id", "sent")
        return True, mid
    return False, data.get("error", {}).get("message", r.text)


PAGE = """
<!doctype html>
<html lang="ur">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhatsApp Broadcast - Women Comforts</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, Arial, sans-serif; background:#f0f2f5; margin:0; padding:24px; color:#111; }
  .card { max-width:760px; margin:0 auto; background:#fff; border-radius:14px; padding:24px 26px; box-shadow:0 2px 14px rgba(0,0,0,.08); }
  h1 { font-size:20px; margin:0 0 4px; }
  .sub { color:#667; font-size:13px; margin-bottom:20px; }
  label { display:block; font-weight:600; font-size:14px; margin:14px 0 6px; }
  input, textarea { width:100%; padding:11px 12px; border:1px solid #ccd; border-radius:9px; font-size:14px; font-family:inherit; }
  textarea { min-height:150px; resize:vertical; }
  .row { display:flex; gap:14px; }
  .row > div { flex:1; }
  button { margin-top:20px; width:100%; padding:13px; background:#25D366; color:#fff; border:0; border-radius:10px; font-size:16px; font-weight:700; cursor:pointer; }
  button:hover { background:#1eb457; }
  .hint { color:#889; font-size:12px; margin-top:6px; }
  table { width:100%; border-collapse:collapse; margin-top:22px; font-size:13px; }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #eee; }
  .ok { color:#1a7f37; font-weight:600; }
  .fail { color:#c0392b; font-weight:600; }
  .summary { margin-top:18px; font-weight:700; }
</style>
</head>
<body>
<div class="card">
  <h1>📣 WhatsApp Broadcast</h1>
  <div class="sub">Approved template ko list ke sab numbers pe bhejo — naye numbers samet.</div>
  <form method="post">
    <div class="row">
      <div>
        <label>Template name</label>
        <input name="template" value="{{ template }}" placeholder="order_management" required>
      </div>
      <div>
        <label>Language code</label>
        <input name="lang" value="{{ lang }}" placeholder="en" required>
      </div>
    </div>

    <label>Numbers (ek line par ek)</label>
    <textarea name="numbers" placeholder="923001234567
923019876543,Faisal
923394015555,Neelam">{{ numbers }}</textarea>
    <div class="hint">Format: <b>number</b> ya <b>number,name</b> (agar template mein {{'{{1}}'}} variable ho). Country code ke sath, bina + ke.</div>

    <label>Panel PIN</label>
    <input name="pin" type="password" placeholder="PIN" required>

    <button type="submit">Send Broadcast</button>
  </form>

  {% if results is not none %}
    {% set sent = results | selectattr('1') | list | length %}
    <div class="summary">✅ Sent: {{ sent }} &nbsp; | &nbsp; ❌ Failed: {{ results|length - sent }}</div>
    <table>
      <tr><th>Number</th><th>Status</th><th>Detail</th></tr>
      {% for num, ok, info in results %}
        <tr>
          <td>{{ num }}</td>
          <td class="{{ 'ok' if ok else 'fail' }}">{{ 'SENT' if ok else 'FAILED' }}</td>
          <td>{{ info }}</td>
        </tr>
      {% endfor %}
    </table>
  {% endif %}
</div>
</body>
</html>
"""


def form_defaults():
    return {
        "template": request.form.get("template", "order_management"),
        "lang": request.form.get("lang", "en"),
        "numbers": request.form.get("numbers", ""),
    }


@app.route("/", methods=["GET", "POST"])
def home():
    results = None
    if request.method == "POST":
        if request.form.get("pin") != ACCESS_PIN:
            results = [("—", False, "Ghalat PIN")]
            return render_template_string(PAGE, results=results, **form_defaults())

        tmpl = request.form.get("template", "").strip()
        lang = (request.form.get("lang", "en").strip() or "en")
        raw  = request.form.get("numbers", "")

        results = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts  = [p.strip() for p in line.split(",")]
            number = parts[0].replace("+", "").replace(" ", "")
            var    = parts[1] if len(parts) > 1 else ""
            if not number:
                continue
            ok, info = send_template(number, tmpl, lang, var)
            results.append((number, ok, info))
            time.sleep(0.5)  # rate-limit safe

    return render_template_string(PAGE, results=results, **form_defaults())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
