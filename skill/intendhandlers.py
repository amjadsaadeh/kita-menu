import datetime
import logging

from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name, request_util
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.handler_input import HandlerInput

from google.cloud import firestore, storage


db = firestore.Client()


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = 'Willkommen beim Kita Essenplan.'

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Willkommen", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response

class FoodForOneDayIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("FoodForOneDay")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        day = request_util.get_slot_value(handler_input, 'day')

        weekdays = ('Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag')
        if day not in weekdays:
            if day is None or day.lower() == 'heute':
                weekday_idx = datetime.datetime.today().weekday()
            elif day.lower() == 'morgen':
                weekday_idx = datetime.datetime.today().weekday() + 1
            elif day.lower() == 'übermorgen':
                weekday_idx = datetime.datetime.today().weekday() + 2
            elif day.lower() == 'gestern':
                weekday_idx = datetime.datetime.today().weekday() - 1
            elif day.lower() == 'vorgestern':
                weekday_idx = datetime.datetime.today().weekday() - 2
            
            day = weekdays[weekday_idx % len(weekdays)]
        
        # TODO connect to firestore to get the food
        speech_text = f"Der angefragete Tag ist {day}"

        user = handler_input['request_envelope']['session']['user']
        user_id = user.attribute_map['user_id']
        menu_doc_ref = db.collection(u'menus').document(user_id)
        cur_week = datetime.datetime.now().isocalendar()[1]
        menu_doc = menu_doc_ref.get().to_dict()
        if menu_doc is None:
            logging.info('Cannot find user with id %s', user_id)
            card_title = 'Kita Speiseplan Fehler'
            speech_text = 'Der angegebener Benutzer wurde leider nicht gefunden.'
        elif cur_week != menu_doc['cw']:
            card_title = 'Kein Speiseplan für diese Woche vorhanden'
            speech_text = 'Leider ist für diese Woche noch kein Speiseplan vorhanden. Lade einen neuen hoch, um ihn '+\
                'dir Ansagen lassen zu können.'
        elif day == 'Samstag' or day == 'Sonntag':
            card_title = 'Wochenede'
            speech_text = 'Für das Wochenende gibt es keinen Speiseplan.'
        else:
            food = menu_doc[day]
            card_title = f'Das Essen für heute ist {food}'
            speech_text = f'Heute gibt es: {food}.'


        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard(card_title, speech_text)).set_should_end_session(
            True)
        return handler_input.response_builder.response

class FoodForWeekIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("FoodForWeek")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # TODO impleement  one day
        speech_text = "Hello World"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            True)
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Frage mich wann welches Essen ansteht. Frage zum Beispiel: Was gibt es heute zu Essen?"

        handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(
            SimpleCard("Hilfe", speech_text))
        return handler_input.response_builder.response

class CancelAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Auf Wiedersehen"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Auf Wiedersehen", speech_text)).set_should_end_session(True)
        return handler_input.response_builder.response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # any cleanup logic goes here

        return handler_input.response_builder.response

class AllExceptionHandler(AbstractExceptionHandler):

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        # Log the exception in CloudWatch Logs
        print(exception)

        speech = "Entschuldigung, ich habe dich nicht richtig verstanden"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response
