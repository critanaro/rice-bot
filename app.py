#Python libraries that we need to import for our bot
from __future__ import print_function
from flask import Flask, request
from pymessenger.bot import Bot
import random
import sys
import os 
import json
import csv

from wit import Wit
access_token = "GGDBZAV5X6J5CJBCKOOLWWWMMMMSHTHR"
wit_client = Wit(access_token)

app = Flask(__name__) ## This is how we create an instance of the Flask class for our app

ACCESS_TOKEN = 'EAAKMgA79MiwBAJpvCa0fOiEhkuHux94c7dwgzOZCvGR8f0pxoZB5csi3o6rPkZAd30MRGmogLHMuF409B954pDl3EgITLzn0qmn5TLlSUEOobdvUZBT1ZCJT2BvYzlYGhrJLQRi6xUd0ZCjyRC75uhhk1lcH1WZCmvy7ZC2TQOhx3dyJyA8yGlme'   #ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = 'TESTINGTOKEN' ## Replace 'VERIFY_TOKEN' with your verify token
bot = Bot(ACCESS_TOKEN) ## Create an instance of the bot

HELP_MESSAGE = "I can provide information about dining options, allergies, and schedules here at Rice!"
EXAMPLES = ["what can I eat at West?", "where can I find vegetarian food?", "which serveries are open today?"]
dining_data_file = "./data/diningData-2018-09-15T19-54-14Z.csv" # TODO: generate based on date
EATERIES = ["west", "north", "south", "seibel", "sid", "baker", "sammy's"]
CONFIDENCE_THRESH = .7

def help_statement():
    return HELP_MESSAGE + " Ask me a question like \"" + random.choice(EXAMPLES) + "\""

def verify_fb_token(token_sent):
    ## Verifies that the token sent by Facebook matches the token sent locally
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def dining_reader(dining_data_file):
    dining_data = []
    with open(dining_data_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            dining_data.append(row)

        return dining_data
    return []

def is_open(servery, dining_data):
    for row in dining_data:
        if row[0].lower() == servery:
            if row[1] == "true":
                words = row[2].split()
                if words[1].lower() != "available":
                    return True

    return False

def menu_options(servery, dining_data):
    options = []
    for row in dining_data:
        if row[0].lower() == servery:
            if row[2]:
                options.append(row[2].strip('\"'))

    return options

def print_menu(servery, dining_data):
    menu = menu_options(servery, dining_data)
    menu_text = ""
    if len(menu) > 0:
        menu_text += servery.capitalize() + " is serving "
        for m in range(len(menu)):
            menu_text += menu[m]
            if m < len(menu) - 2:
                menu_text += ", "
            elif m == len(menu) - 2:
                menu_text += " and "
    return menu_text

def servery_food_find(food, dining_data):
    serveries = []
    for row in dining_data:
        servery = row[0].lower()
        if ((food in row[3].lower().split()) or (food in row[2].lower().split())) and servery not in serveries:
            serveries.append(servery)
    return serveries

def single_servery_food_find(food, servery, dining_data):
    meals = []
    for row in dining_data:
        serv = row[0].lower()
        if servery == serv:
            if food in row[2].lower().split() or food in row[3].lower().split():
                meals.append(row[2])

    return meals

def servery_food_exclude(food, dining_data):
    serveries = []
    for row in dining_data:
        servery = row[0].lower()
        if (food not in row[3].lower().split()) and (food not in row[2].lower().split()) and servery not in serveries:
            serveries.append(servery)

    return serveries

def single_servery_food_exclude(food, servery, dining_data):
    meals = []
    for row in dining_data:
        serv = row[0].lower()
        if servery == serv:
            if food not in row[2].lower().split() and food not in row[3].lower().split():
                meals.append(row[2])

    return meals

# Chooses a message to send to the user
def get_response_text(message):
    message_text = message['text']

    response_message = ""

    nlp_response = wit_client.message(message_text)

    with open('nlp_response_wit.txt', 'w') as file:
        file.write(json.dumps(nlp_response))

    if ('entities' in nlp_response):

        nlp_entities = nlp_response['entities']

        dining_data = dining_reader(dining_data_file)

        eating = False
        schedule = []
        time_input = []
        serveries = []
        mealtype_input = []
        foodtype_input = []
        diet_input = []

        if ('eating' in nlp_entities and nlp_entities['eating'][0]['confidence'] > CONFIDENCE_THRESH):
            #response_message += "I am " + str(round(nlp_entities['eating'][0]['confidence'] * 100)) + \
            #                    "% confident you are talking about eating\n"
            
            # If the user provided no information other than indication that they are talking about eating
            eating = True         

        if ('schedule' in nlp_entities):
            """
            response_message += "I am " + str(round(nlp_entities['schedule'][0]['confidence'] * 100)) + \
                                "% confident you are talking about schedules\n"
            """
            entity = nlp_entities['schedule']
            for s in entity:
                if s['confidence'] > CONFIDENCE_THRESH:
                    schedule.append(s['value'].lower().strip())

        if ('datetime' in nlp_entities):
            """
            response_message += "I am " + str(round(nlp_entities['datetime'][0]['confidence'] * 100)) + \
                                "% confident you are talking about date and time\n"
            """
            entity = nlp_entities['datetime']
            for t in entity:
                if t['confidence'] > CONFIDENCE_THRESH:
                    time_input.append(t['value'])

        if ('serveries' in nlp_entities):
            #response_message += "I am " + str(round(nlp_entities['serveries'][0]['confidence'] * 100)) + \
            #                    "% confident you are talking about serveries\n"

            entity = nlp_entities['serveries']
            serveries = []
            for s in entity:
                if s['confidence'] > CONFIDENCE_THRESH:
                    servery = s['value'].lower().strip()

                    if servery == "sammys":
                        servery = "sammy's"
                    elif servery == "sid richardson":
                        servery = "sid"
                    elif servery == "duncan":
                        servery = "west"
                    elif servery == "mcmurtry":
                        servery = "west"
                    elif servery == "martel":
                        servery = "north"
                    elif servery == "jones":
                        servery = "north"
                    elif servery == "brown":
                        servery = "north"
                    elif servery == "will rice":
                        servery = "seibel"
                    elif servery == "lovett":
                        servery = "seibel"
                    elif servery == "hanszen":
                        servery = "south"
                    elif servery == "weiss":
                        servery = "south"

                    serveries.append(servery)

        if ('mealtype' in nlp_entities):
            response_message += "I am " + str(round(nlp_entities['mealtype'][0]['confidence'] * 100)) + \
                                "% confident you are talking about meals\n"

            entity = nlp_entities['mealtype']
            for m in entity:
                if m['confidence'] > CONFIDENCE_THRESH:
                    mealtype_input.append(m['value'])


        if ('foodtype' in nlp_entities):
            """
            response_message += "I am " + str(round(nlp_entities['foodtype'][0]['confidence'] * 100)) + \
                                "% confident you are talking about foods\n"
            """
            entity = nlp_entities['foodtype']
            for f in entity:
                if f['confidence'] > CONFIDENCE_THRESH:
                    foodtype_input.append(f['value'])

        if ('dietary' in nlp_entities):
            """
            response_message += "I am " + str(round(nlp_entities['dietary'][0]['confidence'] * 100)) + \
                                "% confident you are talking about dietary restrictions\n"
            """
            entity = nlp_entities['dietary']
            for d in entity:
                if d['confidence'] > CONFIDENCE_THRESH:
                    diet_input.append(d['value'])

        ##### CREATING THE MESSAGE #####
        if diet_input or foodtype_input:
            # Determine whether we should look for foods or exclude foods
            inclusion = False
            
            diets = foodtype_input[:]

            if diet_input:
                if "vegetarian" in diet_input:
                    inclusion = True
                    diets.append("vegetarian")

                if "vegan" in diet_input:
                    inclusion = True
                    diets.append("vegan")
            else:
                inclusion = True

            # If no specific servery has been specified, look in them all
            if not serveries:
                for diet in diets:
                    found_serveries = []
                    if inclusion:
                        found_serveries = servery_food_find(diet, dining_data)
                    else:
                        found_serveries = servery_food_exclude(diet, dining_data)

                    for serv in range(len(found_serveries)):
                        response_message += found_serveries[serv].capitalize()
                        if serv < len(found_serveries) - 2:
                            response_message += ", "
                        elif serv == len(found_serveries) - 2:
                            response_message += " and "

                    if len(found_serveries) > 1:
                        response_message += " have "
                    else:
                        response_message += " has "

                    response_message += diet

                    if not inclusion:
                        response_message += " free"

                    response_message += " options today.\n \n"

            # If serveries have been specified
            else:
                for diet in diets:
                    for servery in serveries:
                        if is_open(servery, dining_data):
                            found_meals = []
                            if inclusion:
                                found_meals = single_servery_food_find(diet, servery, dining_data)
                            else:
                                found_meals = single_servery_food_exclude(diet, servery, dining_data)

                            num_meals = len(found_meals)
                            if num_meals > 0:
                                response_message += servery.capitalize() + " is serving "
                                for m in range(num_meals):
                                    response_message += found_meals[m]
                                    if m < num_meals - 2:
                                        response_message += ", "
                                    elif m == num_meals - 2:
                                        response_message += " and "

                                response_message += " today.\n"

                            else: # The servery has no options of this diet
                                response_message += servery.capitalize() + " is not serving any " + diet
                                if not inclusion:
                                    response_message += " free"
                                response_message += " food today.\n \n"

        # Print the menus
        elif (serveries):
            for servery in serveries:
                if servery in EATERIES:
                    if is_open(servery, dining_data):
                        menu_text = print_menu(servery, dining_data)
                        if menu_text:
                            response_message += menu_text + " today.\n"
                        else:
                            response_message += "We don't know the menu for " + servery.capitalize() + " right now.\n \n"

                    # If the servery is closed
                    else:
                        response_message += servery.capitalize() + " is closed today.\n \n"

                # If the eatery is unrecognized
                elif len(nlp_entities) == 1 or (len(nlp_entities) == 2 and "eating" in nlp_entities):
                    response_message += "It seems like you're interested in serveries. " + help_statement() + "\n"

        # General statement regarding eating
        elif (eating and len(nlp_entities) == 1):
            response_message = "It seems like you're interested in eating. " + help_statement()


    if not response_message:
        response_message = "I don't understand that statement. " + help_statement()

    return response_message
    """
    entity1 = firstEntity(message['nlp'])
    if (entity1 and 'greeting' in entity1):
        return "Hi! This is identified as a greeting by built in NLP"
    elif (entity1 and 'sentiment' in entity1):
        return "This is a sentiment, as defined by NLP"
    else:
        return "Hack on!"
    """

"""
with open('employee_birthday.txt') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
            line_count += 1
    print(f'Processed {line_count} lines.')
"""

# Checks whether the first entitiy is 'name' or not
def firstEntity(nlp):
    if nlp and 'entities' in nlp:
        return nlp['entities']
    else:
        return False

## Send text message to recipient
def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response) ## Sends the 'response' parameter to the user
    return "Message sent"

## This endpoint will receive messages 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    ## Handle GET requests
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token") ## Facebook requires a verify token when receiving messages
        return verify_fb_token(token_sent)

    ## Handle POST requests
    else: 
        output = request.get_json() ## get whatever message a user sent the bot
        with open('json_in_message.txt', 'w') as outfile:
            json.dump(output, outfile)

        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):
                    recipient_id = message['sender']['id'] ## Facebook Messenger ID for user so we know where to send response back to

                    response_text = get_response_text(message['message'])
                    send_message(recipient_id, response_text)

        return "Message Processed"

## Ensures that the below code is only evaluated when the file is executed, and ignored if the file is imported
if __name__ == "__main__": 
    app.run() ## Runs application