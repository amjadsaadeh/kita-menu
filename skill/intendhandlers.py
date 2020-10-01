import datetime
import logging

import requests

from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name, request_util
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard, LinkAccountCard
from ask_sdk_core.handler_input import HandlerInput

from google.cloud import firestore


db = firestore.Client()


def get_amzon_user_id(handler_input):
    """
    Extracts the amazon user id from handler input

    Parameters
    ----------
    handler_input : [type]
        [description]

    Returns
    -------
    [type]
        amazon user id as string or None if no account is linked
    """

    account_linking_token = request_util.get_account_linking_access_token(handler_input)
    if account_linking_token is None:
        return None

    r = requests.get('https://api.amazon.com/user/profile', params={'access_token': account_linking_token})
    response = r.json()
    user_id = response['user_id']
    return user_id

def generate_account_linking_card(handler_input):
    handler_input.response_builder.speak(speech_text).set_card(
        LinkAccountCard()).set_should_end_session(
        True)
    return handler_input.response_builder.response

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

        user_id = get_amzon_user_id(handler_input)
        if user_id is None:
            # We got account linking request
            return generate_account_linking_card(handler_input)

        menu_doc_ref = db.collection(u'menus').document(user_id)
        cur_week = datetime.datetime.now().isocalendar()[1]
        menu_doc = menu_doc_ref.get().to_dict()
        if menu_doc is None:
            logging.warn('Cannot find user with id %s', user_id)
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
            food = menu_doc['menu'][day]
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
        user_id = get_amzon_user_id(handler_input)
        if user_id is None:
            # We got account linking request
            return generate_account_linking_card(handler_input)

        menu_doc_ref = db.collection(u'menus').document(user_id)
        cur_week = datetime.datetime.now().isocalendar()[1]
        menu_doc = menu_doc_ref.get().to_dict()
        if menu_doc is None:
            logging.warn('Cannot find user with id %s', user_id)
            card_title = 'Kita Speiseplan Fehler'
            speech_text = 'Der angegebener Benutzer wurde leider nicht gefunden. Loggen Sie sich bitte initial auf '+\
                'der Website ein.'
        elif cur_week != menu_doc['cw']:
            card_title = 'Kein Speiseplan für diese Woche vorhanden'
            speech_text = 'Leider ist für diese Woche noch kein Speiseplan vorhanden. Lades Sie einen neuen hoch, '+\
                'um ihn dir Ansagen lassen zu können.'
        else:
            card_title = 'Das Essen für diese Woche'
            parts = ['Am {:s} gibt es {:s}'.format(day, food) for day, food in menu_doc['menu']]
            speech_text = '\n'.join(parts)

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard(card_title, speech_text)).set_should_end_session(
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
        logging.exception(exception)

        speech = "Entschuldigung, ich habe dich nicht richtig verstanden"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response
