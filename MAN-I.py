import pyttsx3
import speech_recognition as sr
import random
import webbrowser
import datetime
from plyer import notification
import pyautogui
import wikipedia
import pywhatkit as pwk
import user_config
import smtplib, ssl
import open_ai as ai
import img_gen
import mtranslate
import sys
import signal
import time

sys.stdout.reconfigure(encoding='utf-8')

# Global variable to control the main loop
running = True

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    global running
    print("Stopping MAN-I...", flush=True)
    running = False
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty("rate", 130)


def speak(audio):
    try:
        engine.say(audio)
        engine.runAndWait()
        time.sleep(1.0)
    except Exception as e:
        print(f"Speech error: {e}", flush=True)


def command():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    
    content = " "
    while content == " " and running:
        try:
            with sr.Microphone() as source:
                print("Say Something!!", flush=True)
                r.adjust_for_ambient_noise(source, duration=0.2)
                
                try:
                    audio = r.listen(source, timeout=10, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    print("Listening timeout, please try again!", flush=True)
                    continue

            time.sleep(0.2)
            
            try:
                content = r.recognize_google(audio, language='en-US')
                
                hindi_words = ['batao', 'kya', 'hai', 'naam', 'tumhara', 'mera', 'kaise', 'kahan', 'kab', 'kyun', 'aap', 'main', 'hum', 'tum']
                is_hindi = any(word in content.lower() for word in hindi_words)
                
                if is_hindi:
                    print("Detected Hindi in English recognition: " + content, flush=True)
                    try:
                        hindi_content = r.recognize_google(audio, language='hi-IN')
                        print("You said (Hindi): " + hindi_content, flush=True)
                        
                        translated_content = mtranslate.translate(hindi_content, from_language='hi', to_language='en')
                        print("Translated to English: " + translated_content, flush=True)
                        
                        return translated_content
                    except:
                        print("Using original recognition as fallback", flush=True)
                        return content
                else:
                    print("You said (English): " + content, flush=True)
                    return content
                
            except sr.UnknownValueError:
                try:
                    content = r.recognize_google(audio, language='hi-IN')
                    print("You said (Hindi): " + content, flush=True)
                    
                    translated_content = mtranslate.translate(content, from_language='hi', to_language='en')
                    print("Translated to English: " + translated_content, flush=True)
                    
                    return translated_content
                    
                except Exception as e:
                    print("Please try again !!", flush=True)
                    content = " "
            except sr.RequestError as e:
                print("Could not request results; check your internet connection", flush=True)
                content = " "
            except Exception as e:
                print("Please try again !!", flush=True)
                content = " "
                
        except Exception as e:
            print("Audio error, retrying...", flush=True)
            content = " "
            time.sleep(0.5)
    
    return content


def main_process():
    global running
    jarvis_chat = []
    print("MAN-I is now running and listening...", flush=True)
    
    while running:
        time.sleep(0.5)
        
        try:
            request = command().lower()
        except Exception as e:
            print("Command recognition error, retrying...", flush=True)
            continue
            
        if any(phrase in request for phrase in ["hi", "hello"]):
            speak("welcome, How can I help you.")
    
        if "how are you" in request:
            speak("I am fine, How are you my dear.")
    
        if any(phrase in request for phrase in ["namaste", "tum kaise ho", "app kaise ho"]):
            speak("namaste main acha hun, app kaise hain.")
        
        elif "play music" in request:
            speak("playing music")
            songs = (1, 2, 3, 4, 5)
            song = random.randint(1, 5)
            if song == 1:
                webbrowser.open("https://youtu.be/cWBnahDXnJs")
            elif song == 2:
                webbrowser.open("https://youtu.be/i-VNwyZm8r0")
            elif song == 3:
                webbrowser.open("https://youtu.be/E6IDh_jxSB8")
            elif song == 4:
                webbrowser.open("https://youtu.be/WZ91k09bvdk")
            elif song == 5:
                webbrowser.open("https://youtu.be/O_X8HrFaejM")

        elif "current time" in request:
            now_time = datetime.datetime.now().strftime("%H:%M")
            speak("current time is " + str(now_time))

        elif "current day" in request:
            now_time = datetime.datetime.now().strftime("%d:%m")
            speak("current date is " + str(now_time))

        elif "new task" in request:
            task = request.replace("new task", "")
            task = task.strip()
            if task != "":
                speak("Adding task :" + task)
                with open("todo.txt", "a") as file:
                    file.write(task + "\n")
        
        elif "my task" in request:
            with open("todo.txt", "r") as file:
                speak("work we have to do today is :" + file.read())
        
        elif "today job" in request:
            with open("todo.txt", "r") as file:
                tasks = file.read()
            try:
                notification.notify(
                    title="Today's Work",
                    message=tasks,
                    timeout=10
                )
            except Exception as e:
                print(f"Notification error: {e}", flush=True)
                speak("Your tasks are: " + tasks)
            
        elif "open" in request:
            query = request.replace("open", "")
            pyautogui.press("super")
            pyautogui.typewrite(query)
            pyautogui.sleep(2)
            pyautogui.press("enter") 

        elif "wikipedia" in request:
            request = request.replace("jarvis", "")
            request = request.replace("search wikipedia", "")
            print(request, flush=True)
            try:
                result = wikipedia.summary(request, sentences=2)
                print(result, flush=True)
                speak(result)
            except Exception as e:
                speak("Sorry, I couldn't find that on Wikipedia")

        elif "search google" in request:
            request = request.replace("jarvis", "")
            request = request.replace("search google", "")
            webbrowser.open("https://www.google.com/search?q=" + request)
            
            
        elif "send whatsapp" in request:
            try:
                pwk.sendwhatmsg_instantly("+918847892002", "Hi, This is Man-I")
            except Exception as e:
                speak("Sorry, couldn't send WhatsApp message")
       
        elif "send email" in request:
            try:
                pwk.send_mail("contact.maneye@gmail.com", user_config.gmail_password, " MAN-I ", "Hello, This Is Man-I From VsCode And This Is A Sample Mail,", "jaganmohankhuntia0@gmail.com")
                speak("email sent successfully")
            except Exception as e:
                speak("Sorry, couldn't send email")
            
        elif "image" in request:
            request = request.replace("jarvis", "")
            try:
                img_gen.generate_image(request)
            except Exception as e:
                speak("Sorry, couldn't generate image")

        elif "ask ai" in request:
            jarvis_chat = []
            request = request.replace("jarvis", "")
            request = request.replace("ask ai", "")
            jarvis_chat.append({"role": "user", "content": request})
            try:
                response = ai.send_request(jarvis_chat)
                if response:
                    speak(response)
                else:
                    speak("Sorry, I couldn't process that request.")
            except Exception as e:
                speak("Sorry, there was an error processing your request.")
            time.sleep(0.5)

        elif "clear chat" in request:
            jarvis_chat = []
            speak("chat cleared")
            time.sleep(0.5)
        
        elif "stop listening" in request or "exit" in request or "quit" in request:
            speak("Goodbye! Shutting down.")
            running = False
            break
            
        else:
            # Keep chat history manageable (max 10 exchanges)
            if len(jarvis_chat) > 20:
                jarvis_chat = jarvis_chat[-10:]
                
            request = request.replace("jarvis", "")
            jarvis_chat.append({"role": "user", "content": request})
            
            try:
                response = ai.send_request(jarvis_chat)
                if response:
                    jarvis_chat.append({"role": "assistant", "content": response})
                    speak(response)
                else:
                    speak("Sorry, I couldn't process that request.")
                    jarvis_chat.pop()
            except Exception as e:
                speak("Sorry, there was an error processing your request.")
                jarvis_chat.pop()
            
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        main_process()
    except KeyboardInterrupt:
        print("\nMAN-I stopped by user", flush=True)
    except Exception as e:
        print(f"Fatal error: {e}", flush=True)
    finally:
        print("MAN-I shutting down...", flush=True)