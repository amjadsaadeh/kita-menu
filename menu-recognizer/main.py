import base64
import os
import json
import logging
import datetime
from pathlib import Path

from flask import Flask, request

from google.cloud import firestore

from recognizer import process_image


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        logging.error(msg)
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        logging.error(msg)
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            data = json.loads(base64.b64decode(pubsub_message['data']).decode())
        except Exception as e:
            msg = 'Invalid Pub/Sub message: data property is not valid base64 encoded JSON'
            logging.exception(e)
            return f'Bad Request: {msg}', 400

        # Validate the message is a Cloud Storage event.
        if not data['name'] or not data['bucket']:
            msg = 'Invalid Cloud Storage notification: expected name and bucket properties'
            logging.error(msg)
            return f'Bad Request: {msg}', 400
        try:
            user_id = Path(data['name']).stem
            db = firestore.Client()

            progress_doc_ref = db.collection(u'progress').document(user_id)
            progress_doc_ref.set({'state': 'processing'})

            menu = process_image(data['bucket'], data['name'], 'de') # TODO make language configurable
            cw = datetime.date.today().isocalendar()[1]

            menu_doc_ref = db.collection(u'menus').document(user_id)
            menu_doc_ref.set({
                'cw': cw,
                'menu': menu
            })

            progress_doc_ref = db.collection(u'progress').document(user_id)
            progress_doc_ref.set({'state': 'complete'})

            return ('', 204)

        except Exception as e:
            logging.exception(e)
            return ('', 500)

    return ('', 500)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)
