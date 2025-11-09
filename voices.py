import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
for i in voices:
    print(i)
    
# import pyttsx3

# engine = pyttsx3.init()
# voices = engine.getProperty('voices')
# for voice in voices:
#     print(f"Voice: {voice.name}") 
# 
# 0 -8 