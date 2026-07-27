import datetime
import json
import os
import re
import smtplib
import threading
import time
import webbrowser
from email.message import EmailMessage
from urllib.parse import quote_plus

import pyttsx3
import requests
import speech_recognition as sr

try:
    from config import WEATHER_API_KEY, EMAIL_ADDRESS, EMAIL_APP_PASSWORD
except ImportError:
    WEATHER_API_KEY = ""
    EMAIL_ADDRESS = ""
    EMAIL_APP_PASSWORD = ""



# CONFIGURATION


CUSTOM_COMMANDS_FILE = "custom_commands.json"

recognizer = sr.Recognizer()

engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")

if voices:
    engine.setProperty("voice", voices[0].id)



# TEXT TO SPEECH


def speak(text):
    """Print and speak the assistant response."""

    print(f"\nAssistant: {text}")

    engine.say(text)
    engine.runAndWait()



# SPEECH RECOGNITION


def listen():
    """Listen through microphone and convert speech to text."""

    try:
        with sr.Microphone() as source:

            print("\nListening...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.7
            )

            try:
                audio = recognizer.listen(
                    source,
                    timeout=6,
                    phrase_time_limit=10
                )

            except sr.WaitTimeoutError:
                speak("I did not hear anything. Please try again.")
                return None

        print("Recognizing...")

        command = recognizer.recognize_google(audio)

        command = command.lower().strip()

        print(f"You: {command}")

        return command

    except sr.UnknownValueError:

        speak(
            "Sorry, I could not understand your voice. "
            "Please repeat."
        )

        return None

    except sr.RequestError:

        speak(
            "The speech recognition service is unavailable. "
            "Please check your internet connection."
        )

        return None

    except Exception as error:

        print(f"Microphone error: {error}")

        speak("There was a problem accessing the microphone.")

        return None



# GREETING


def greet_user():

    hour = datetime.datetime.now().hour

    if hour < 12:
        greeting = "Good morning"

    elif hour < 17:
        greeting = "Good afternoon"

    else:
        greeting = "Good evening"

    speak(
        f"{greeting}! I am your advanced Python voice assistant. "
        "How can I help you?"
    )



# DATE AND TIME

def tell_time():

    current_time = datetime.datetime.now().strftime("%I:%M %p")

    speak(f"The current time is {current_time}.")


def tell_date():

    current_date = datetime.datetime.now().strftime(
        "%A, %d %B %Y"
    )

    speak(f"Today is {current_date}.")



# WEB SEARCH

def search_web(command):

    phrases = [
        "search for",
        "search about",
        "look up",
        "find information about",
        "google",
        "search"
    ]

    query = command

    for phrase in phrases:

        if phrase in query:

            query = query.replace(
                phrase,
                "",
                1
            )

            break

    query = query.strip()

    if not query:

        speak("What would you like me to search for?")

        query = listen()

        if not query:
            return

    speak(f"Searching the web for {query}.")

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    webbrowser.open(url)



# OPEN WEBSITES

def open_website(command):

    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://github.com",
        "linkedin": "https://www.linkedin.com",
        "stackoverflow": "https://stackoverflow.com"
    }

    for website, url in websites.items():

        if website in command:

            speak(f"Opening {website}.")

            webbrowser.open(url)

            return

    speak("I do not have that website configured.")



# LIVE WEATHER


def extract_city(command):

    patterns = [
        r"weather in (.+)",
        r"weather at (.+)",
        r"temperature in (.+)",
        r"temperature at (.+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, command)

        if match:
            return match.group(1).strip()

    return None


def get_weather(city=None):

    if not WEATHER_API_KEY or WEATHER_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":

        speak(
            "The weather API key has not been configured."
        )

        return

    if not city:

        speak("Which city's weather would you like?")

        city = listen()

        if not city:
            return

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code == 404:

            speak(f"I could not find the city {city}.")
            return

        if response.status_code == 401:

            speak(
                "The weather API key is invalid or not active yet."
            )
            return

        response.raise_for_status()

        data = response.json()

        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]

        description = data["weather"][0]["description"]

        wind_speed = data["wind"]["speed"]

        speak(
            f"The weather in {city} is {description}. "
            f"The temperature is {temperature:.1f} degrees Celsius. "
            f"It feels like {feels_like:.1f} degrees Celsius. "
            f"Humidity is {humidity} percent. "
            f"Wind speed is {wind_speed} meters per second."
        )

    except requests.exceptions.RequestException as error:

        print(f"Weather error: {error}")

        speak(
            "I could not connect to the weather service. "
            "Please check your internet connection."
        )

    except (KeyError, ValueError):

        speak(
            "I received unexpected information "
            "from the weather service."
        )



# TIMED REMINDER


def reminder_alert(message):

    print("\n" + "=" * 55)
    print(f"REMINDER: {message}")
    print("=" * 55)

    speak(f"Reminder! {message}")


def reminder_worker(seconds, message):

    time.sleep(seconds)

    reminder_alert(message)


def set_reminder(command):

    pattern = (
        r"(?:remind me|set (?:a )?reminder)"
        r".*?(?:in|after)\s+"
        r"(\d+)\s*"
        r"(second|seconds|minute|minutes|hour|hours)"
        r"(?:\s+(?:to|for)\s+(.+))?"
    )

    match = re.search(pattern, command)

    if match:

        amount = int(match.group(1))

        unit = match.group(2)

        message = match.group(3)

    else:

        speak(
            "Tell me the reminder duration, "
            "for example, ten seconds."
        )

        duration = listen()

        if not duration:
            return

        duration_match = re.search(
            r"(\d+)\s*"
            r"(second|seconds|minute|minutes|hour|hours)",
            duration
        )

        if not duration_match:

            speak(
                "I could not understand the reminder duration."
            )

            return

        amount = int(duration_match.group(1))

        unit = duration_match.group(2)

        message = None

    if "hour" in unit:

        seconds = amount * 3600

    elif "minute" in unit:

        seconds = amount * 60

    else:

        seconds = amount

    if not message:

        speak("What should I remind you about?")

        message = listen()

        if not message:
            message = "Your reminder is due."

    reminder_thread = threading.Thread(
        target=reminder_worker,
        args=(seconds, message),
        daemon=True
    )

    reminder_thread.start()

    speak(
        f"Reminder set for {amount} {unit}. "
        f"I will remind you to {message}."
    )



# EMAIL


def send_email():

    if (
        not EMAIL_ADDRESS
        or not EMAIL_APP_PASSWORD
        or EMAIL_ADDRESS == "your_test_email@gmail.com"
    ):

        speak(
            "Email credentials have not been configured."
        )

        return

    

    speak("Please enter the recipient email address.")

    recipient = input(
        "\nRecipient email: "
    ).strip()

    if not recipient:

        speak("Recipient email cannot be empty.")
        return

    speak("What is the email subject?")

    subject = listen()

    if not subject:

        subject = input(
            "Subject: "
        ).strip()

    speak("What message would you like to send?")


    body = listen()

    if not body:

        body = input(
            "Message: "
        ).strip()

    if not body:

        speak("The email message cannot be empty.")
        return

    print("\n" + "=" * 50)
    print("EMAIL PREVIEW")
    print("=" * 50)

    print(f"To      : {recipient}")
    print(f"Subject : {subject}")
    print(f"Message : {body}")

    print("=" * 50)

    speak("Should I send this email?")

    confirmation = listen()

    if not confirmation:

        confirmation = input(
            "Send? (yes/no): "
        ).lower()

    if "yes" not in confirmation:

        speak("Email cancelled.")
        return

    try:

        email_message = EmailMessage()

        email_message["From"] = EMAIL_ADDRESS
        email_message["To"] = recipient
        email_message["Subject"] = subject

        email_message.set_content(body)

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_APP_PASSWORD
            )

            server.send_message(
                email_message
            )

        speak("The email was sent successfully.")

    except Exception as error:

        print(f"Email error: {error}")

        speak(
            "I could not send the email. "
            "Please check your email configuration."
        )


# GENERAL KNOWLEDGE Q&A


def clean_knowledge_question(question):

    prefixes = [
        "who is ",
        "what is ",
        "who was ",
        "what was ",
        "tell me about "
    ]

    cleaned = question.lower().strip()

    for prefix in prefixes:

        if cleaned.startswith(prefix):

            cleaned = cleaned[len(prefix):]

            break

    return cleaned.strip()


def answer_general_question(question):

    topic = clean_knowledge_question(question)

    if not topic:

        speak("Please ask me a complete question.")
        return

    speak(f"Let me find information about {topic}.")

    try:

        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + quote_plus(topic)
        )

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                    "OIBSIP-Voice-Assistant/1.0"
            }
        )

        if response.status_code == 200:

            data = response.json()

            answer = data.get("extract")

            if answer:

                sentences = re.split(
                    r"(?<=[.!?])\s+",
                    answer
                )

                short_answer = " ".join(
                    sentences[:2]
                )

                speak(short_answer)

                return

        speak(
            "I could not find a direct answer. "
            "I will search the web instead."
        )

        search_web(f"search for {topic}")

    except requests.exceptions.RequestException:

        speak(
            "The knowledge service is unavailable. "
            "I will search the web instead."
        )

        search_web(f"search for {topic}")



# CUSTOM COMMANDS


def load_custom_commands():

    if not os.path.exists(CUSTOM_COMMANDS_FILE):

        return {}

    try:

        with open(
            CUSTOM_COMMANDS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {}


def save_custom_commands(commands):

    try:

        with open(
            CUSTOM_COMMANDS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                commands,
                file,
                indent=4
            )

        return True

    except OSError as error:

        print(f"Custom command error: {error}")

        return False


def add_custom_command():

    speak(
        "What phrase should activate "
        "the custom command?"
    )

    trigger = listen()

    if not trigger:
        return

    speak(
        "What should I say when you use "
        "this command?"
    )

    response = listen()

    if not response:
        return

    commands = load_custom_commands()

    commands[trigger.lower()] = response

    if save_custom_commands(commands):

        speak(
            f"The custom command {trigger} "
            "has been saved successfully."
        )

    else:

        speak(
            "I could not save the custom command."
        )


def execute_custom_command(command):

    commands = load_custom_commands()

    if command.lower() in commands:

        speak(commands[command.lower()])

        return True

    return False



# NATURAL-LANGUAGE INTENT DETECTION


def detect_intent(command):
    """
    Lightweight natural-language intent detection.

    The assistant does not require one exact sentence.
    Different free-form phrases can map to the same intent.
    """

    command = command.lower().strip()

    # EXIT

    exit_phrases = [
        "stop assistant",
        "exit assistant",
        "quit assistant",
        "goodbye",
        "shut down"
    ]

    if any(
        phrase in command
        for phrase in exit_phrases
    ):
        return "exit"


    # CUSTOM COMMAND CREATION

    custom_phrases = [
        "add custom command",
        "create custom command",
        "new custom command"
    ]

    if any(
        phrase in command
        for phrase in custom_phrases
    ):
        return "custom"


    # EMAIL

    email_phrases = [
        "send an email",
        "send email",
        "write an email",
        "email someone"
    ]

    if any(
        phrase in command
        for phrase in email_phrases
    ):
        return "email"


    # REMINDER

    reminder_phrases = [
        "remind me",
        "set reminder",
        "set a reminder"
    ]

    if any(
        phrase in command
        for phrase in reminder_phrases
    ):
        return "reminder"


    # WEATHER

    weather_phrases = [
        "weather",
        "temperature"
    ]

    if any(
        phrase in command
        for phrase in weather_phrases
    ):
        return "weather"


    # TIME

    time_phrases = [
        "what time",
        "current time",
        "tell me the time",
        "time now",
        "what's the time"
    ]

    if any(
        phrase in command
        for phrase in time_phrases
    ):
        return "time"


    # DATE

    date_phrases = [
        "today's date",
        "todays date",
        "current date",
        "tell me the date",
        "what date",
        "what day is it"
    ]

    if any(
        phrase in command
        for phrase in date_phrases
    ):
        return "date"


    # SEARCH

    search_phrases = [
        "search for",
        "search about",
        "look up",
        "google",
        "find information"
    ]

    if any(
        phrase in command
        for phrase in search_phrases
    ):
        return "search"


    # OPEN WEBSITE

    if command.startswith("open "):

        return "website"


    # HELP

    help_phrases = [
        "help",
        "what can you do",
        "show commands",
        "available commands"
    ]

    if any(
        phrase in command
        for phrase in help_phrases
    ):
        return "help"


    # GREETING

    greeting_patterns = [
        r"\bhello\b",
        r"\bhi\b",
        r"\bhey\b",
        r"good morning",
        r"good afternoon",
        r"good evening"
    ]

    if any(
        re.search(pattern, command)
        for pattern in greeting_patterns
    ):
        return "greeting"


    # GENERAL KNOWLEDGE

    knowledge_phrases = [
        "who is ",
        "what is ",
        "who was ",
        "what was ",
        "tell me about "
    ]

    if any(
        command.startswith(phrase)
        for phrase in knowledge_phrases
    ):
        return "knowledge"


    return "unknown"



# HELP


def show_help():

    print(
        """
============================================================
              ADVANCED VOICE ASSISTANT
============================================================

GREETING
  "Hello"
  "Hey assistant"

DATE AND TIME
  "What time is it?"
  "Tell me the current time"
  "What is today's date?"

WEB SEARCH
  "Search for generative AI"
  "Look up Python programming"

OPEN WEBSITE
  "Open YouTube"
  "Open GitHub"
  "Open LinkedIn"

WEATHER
  "What's the weather in Hyderabad?"
  "Tell me the temperature in Delhi"

EMAIL
  "Send an email"

REMINDER
  "Remind me in 10 seconds to drink water"
  "Set a reminder in 5 minutes to study"

GENERAL KNOWLEDGE
  "Who is Alan Turing?"
  "What is artificial intelligence?"
  "Tell me about Python"

CUSTOM COMMAND
  "Add custom command"

OTHER
  "Help"
  "Stop assistant"

============================================================
"""
    )

    speak(
        "I can tell you the date and time, search the web, "
        "open websites, check live weather, send email, "
        "set reminders, answer general knowledge questions, "
        "and create custom commands."
    )



# COMMAND PROCESSING


def process_command(command):

    if not command:

        return True

    # Check user-defined commands first

    if execute_custom_command(command):

        return True

    intent = detect_intent(command)

    print(f"Detected Intent: {intent}")


    if intent == "greeting":

        speak("Hello! How can I help you?")


    elif intent == "time":

        tell_time()


    elif intent == "date":

        tell_date()


    elif intent == "search":

        search_web(command)


    elif intent == "website":

        open_website(command)


    elif intent == "weather":

        city = extract_city(command)

        get_weather(city)


    elif intent == "email":

        send_email()


    elif intent == "reminder":

        set_reminder(command)


    elif intent == "knowledge":

        answer_general_question(command)


    elif intent == "custom":

        add_custom_command()


    elif intent == "help":

        show_help()


    elif intent == "exit":

        speak(
            "Goodbye! Thank you for using "
            "the Python voice assistant."
        )

        return False


    else:

        speak(
            "I am not sure what you mean. "
            "Please try again or say help."
        )


    return True



# MAIN PROGRAM


def main():

    print("=" * 65)
    print("          OASIS INFOBYTE - PYTHON PROGRAMMING")
    print("         TASK 1 - ADVANCED VOICE ASSISTANT")
    print("=" * 65)

    print("\nAdvanced Features:")
    print("  [1] Speech Recognition")
    print("  [2] Text-to-Speech")
    print("  [3] Natural Language Intent Detection")
    print("  [4] Date and Time")
    print("  [5] Web Search")
    print("  [6] Live Weather")
    print("  [7] Email")
    print("  [8] Timed Reminders")
    print("  [9] General Knowledge Q&A")
    print(" [10] Custom Commands")

    print("\nSay 'help' for commands.")
    print("Say 'stop assistant' to exit.\n")

    greet_user()

    running = True

    while running:

        try:

            command = listen()

            if command:

                running = process_command(command)

        except KeyboardInterrupt:

            print("\nAssistant stopped by user.")

            speak("Goodbye!")

            break

        except Exception as error:

            print(f"Unexpected error: {error}")

            speak(
                "An unexpected error occurred. "
                "Please try again."
            )



# PROGRAM ENTRY POINT

if __name__ == "__main__":

    main()