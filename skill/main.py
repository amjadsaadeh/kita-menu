import os

from flask import Flask
from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter

from intendhandlers import *

SKILL_ID = os.environ['ALEXA_SKILL_ID']

app = Flask(__name__)

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(FoodForOneDayIntentHandler())
sb.add_request_handler(FoodForWeekIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(AllExceptionHandler())

skill_adapter = SkillAdapter(skill=sb.create(), skill_id=SKILL_ID, app=app)

@app.route("/", methods=['POST'])
def invoke_skill():
    return skill_adapter.dispatch_request()

if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)
