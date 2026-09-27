import os
import sys
import types
import logging

# urllib3 2.x removed contrib.appengine. Old requests-toolbelt still imports it.
def _shim_urllib3_appengine() -> None:
    try:
        from urllib3.contrib import appengine  # noqa: F401
        return
    except Exception:
        pass
    dummy = types.ModuleType("urllib3.contrib.appengine")
    sys.modules["urllib3.contrib.appengine"] = dummy
    sys.modules["requests.packages.urllib3.contrib.appengine"] = dummy
    try:
        import urllib3.contrib as contrib
        if not hasattr(contrib, "appengine"):
            contrib.appengine = dummy
    except Exception:
        pass


_shim_urllib3_appengine()

from dotenv import load_dotenv
from flask import Flask, request, make_response
from heyoo import WhatsApp

load_dotenv()

app = Flask(__name__)

TOKEN = os.environ.get("TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")

if not TOKEN or not PHONE_NUMBER_ID or not VERIFY_TOKEN:
    raise RuntimeError(
        "Set TOKEN, PHONE_NUMBER_ID, and VERIFY_TOKEN in the environment or .env"
    )

messenger = WhatsApp(TOKEN, phone_number_id=PHONE_NUMBER_ID)
messenger.api_version = API_VERSION
messenger.base_url = f"https://graph.facebook.com/{API_VERSION}"
messenger.v15_base_url = messenger.base_url
messenger.url = f"{messenger.base_url}/{PHONE_NUMBER_ID}/messages"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@app.get("/")
async def verify_token():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        logging.info("Verified webhook")
        response = make_response(request.args.get("hub.challenge"), 200)
        response.mimetype = "text/plain"
        return response
    logging.error("Webhook Verification failed")
    return "Invalid verification token", 403


@app.post("/")
async def hook():
    data = request.get_json(silent=True) or {}
    logging.info("Received webhook data: %s", data)
    try:
        changed_field = messenger.changed_field(data)
        if changed_field == "messages":
            new_message = messenger.is_message(data)
            if new_message:
                mobile = messenger.get_mobile(data)
                name = messenger.get_name(data)
                message_type = messenger.get_message_type(data)
                logging.info(
                    "New Message; sender:%s name:%s type:%s",
                    mobile,
                    name,
                    message_type,
                )
                if message_type == "text":
                    message = messenger.get_message(data)
                    logging.info("Message: %s", message)
                    await messenger.send_message(
                        f"Hi {name}, nice to connect with you", mobile
                    )
                elif message_type == "interactive":
                    message_response = messenger.get_interactive_response(data)
                    interactive_type = message_response.get("type")
                    message_id = message_response[interactive_type]["id"]
                    message_text = message_response[interactive_type]["title"]
                    logging.info("Interactive Message; %s: %s", message_id, message_text)
                elif message_type == "location":
                    message_location = messenger.get_location(data)
                    logging.info(
                        "Location: %s, %s",
                        message_location["latitude"],
                        message_location["longitude"],
                    )
                elif message_type == "image":
                    image = messenger.get_image(data)
                    image_url = await messenger.query_media_url(image["id"])
                    image_filename = await messenger.download_media(
                        image_url, image["mime_type"]
                    )
                    logging.info("%s sent image %s", mobile, image_filename)
                elif message_type == "video":
                    video = messenger.get_video(data)
                    video_url = await messenger.query_media_url(video["id"])
                    video_filename = await messenger.download_media(
                        video_url, video["mime_type"]
                    )
                    logging.info("%s sent video %s", mobile, video_filename)
                elif message_type == "audio":
                    audio = messenger.get_audio(data)
                    audio_url = await messenger.query_media_url(audio["id"])
                    audio_filename = await messenger.download_media(
                        audio_url, audio["mime_type"]
                    )
                    logging.info("%s sent audio %s", mobile, audio_filename)
                elif message_type == "document":
                    file = messenger.get_document(data)
                    file_url = await messenger.query_media_url(file["id"])
                    file_filename = await messenger.download_media(
                        file_url, file["mime_type"]
                    )
                    logging.info("%s sent file %s", mobile, file_filename)
                else:
                    logging.info("%s sent %s", mobile, message_type)
                    logging.info(data)
            else:
                delivery = messenger.get_delivery(data)
                if delivery:
                    logging.info("Message : %s", delivery)
                else:
                    logging.info("No new message")
    except Exception:
        logging.exception("webhook failed")
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
