from datetime import datetime
import re
import threading
import time
from chatbot.chatbot_llm import ChatbotLLM
from langchain.memory import ChatMessageHistory
import json
import requests

class Chatbot:
    def __init__(self, send_response_func, send_image_func, send_data_func, sid, socketio, config):
        print(config)
        self.send_to_client = send_response_func
        self.send_data_to_client = send_data_func
        self.message_history=""
        self.config = config
        self.chat_history = ChatMessageHistory()
        self.innermonologue = []
        self.running = True
        self.details = {}  # Assuming this gets loaded later
        self.socketio = socketio
        self.sid = sid
        self.interrupted = False
        self.prompting = False
        self.lastBotPromptTime = None
        self.lastUserPromptTime = None
        self.send_image_func = send_image_func

    def startThinkingThread(self):
        # Start the inner monologue thread
        self.inner_monologue_thread = threading.Thread(target=self.update_inner_monologue)
        self.inner_monologue_thread.start()


    def startImageGenThread(self):
        self.imagegen_thread = threading.Thread(target=self.update_imagegen)
        self.imagegen_thread.start()

    def kill(self):
        print('disconnect so killing threads')
        self.stop_imagegen_thread()
        self.stop_inner_monologue()

    def process_message(self, message):        
        response = f"Chatbot received message: {message}"
        user_data = {"name":"Jamie", "age":45, "gender":"M", "location":"Earth"}
        message_timestamp = datetime.now().strftime("(%H:%M:%S)")
        self.lastUserPromptTime = datetime.now()

        if(message['type'] == 'text'):
            user_prompt = message['data']
            user_prompt = f"{message_timestamp} {message['data']}"
            self.chat_history.add_user_message(user_data.get('name','') + ':' + user_prompt)
            stringChatHistory = '\n'.join(map(lambda m : m.content, self.chat_history.messages))

            llm_system_prompt = self.resolve_prompt(
                    self.details['SystemPrompt'],
                    user_data,
                    stringChatHistory,
                    user_prompt,
                    '',
                    '\n'.join(self.innermonologue)
                )
            llm_user_prompt = self.resolve_prompt(
                    self.details['UserPrompt'],
                    user_data,
                    stringChatHistory,
                    user_prompt,
                    '',
                    '\n'.join(self.innermonologue)                    
            )
            self.prompting = True  
            llm = ChatbotLLM(self.config)
            response = llm.doPrompt(llm_system_prompt, llm_user_prompt)

            message_timestamp = datetime.now().strftime("(%H:%M:%S)")
            responsemessage = f"{message_timestamp} {response['response']}"
            self.chat_history.add_ai_message(self.details["Name"] + ':' +  responsemessage)
            self.lastBotPromptTime = datetime.now()
            self.send_to_client(response, self.sid)
            self.summarize()
            self.prompting = False
            
        elif(message['type'] == 'command'):
            command = message['data']
            stringChatHistory = '\n'.join(map(lambda m : m.content, self.chat_history.messages))

            llm_system_prompt = self.resolve_prompt(
                    self.details['SystemPrompt'],
                    user_data,
                    stringChatHistory,
                    'Example User Prompt', '', '\n'.join(self.innermonologue)
                )
            llm_user_prompt = self.resolve_prompt(
                    self.details['UserPrompt'],
                    user_data,
                    stringChatHistory,
                    'Example User Prompt', '', '\n'.join(self.innermonologue)         
            )            
            if(command.lower().strip() == 'prompts'):
                self.send_to_client(f"<Prompts>\n<SystemPrompt>\n{llm_system_prompt}\n</SystemPrompt>\n<UserPrompt>\n{llm_user_prompt}\n</UserPrompt></Prompts>", self.sid)
            if(command.lower().strip() == 'thoughts'):
                self.send_to_client(f"<Thoughts>\n{'\n'.join(self.innermonologue)}\n</Thoughts>", self.sid)
            if(command.lower().strip() == 'history'):
                self.send_to_client(f"{stringChatHistory}", self.sid)  
            if(command.lower().strip() == 'image'):
                self.doImage()


    def summarize(self):
        message_count = len(self.chat_history.messages)
        llm = ChatbotLLM(self.config)
        user_data = {"name":"Jamie", "age":45, "gender":"M", "location":"Earth"}
        stringChatHistory = '\n'.join(map(lambda m : m.content, self.chat_history.messages))
    
        llm_system_prompt = self.resolve_prompt(
                self.details['SummarizeSystemPrompt'],
                user_data,
                stringChatHistory,
                'Example User Prompt', '', '\n'.join(self.innermonologue)
            )
        llm_user_prompt = self.resolve_prompt(
                self.details['SummarizeUserPrompt'],
                user_data,
                stringChatHistory,
                'Example User Prompt', '', '\n'.join(self.innermonologue)         
        ) 

        response = llm.doPrompt(llm_system_prompt, llm_user_prompt)        
        print("SUMMARY:")
        print(response)
        summary = response
        
        while(message_count > 7):
            m = self.chat_history.messages.pop(0)
            message_count = len(self.chat_history.messages)
            print('just removed message : ' + m.content)
        




    def load(self, character_details):
        self.details = character_details
        promptInstructions = self.details['PromptInstruction']
        promptInstructions = re.sub(r'\t', '', promptInstructions)
        promptInstructions = re.sub(r'  +', '', promptInstructions)
        self.details['PromptInstruction'] = promptInstructions

    def resolve_prompt(self, prompt, user_info=None, chat_history='', userprompt='', chatsummary='', innermonologue=''):
        current_date = datetime.now().strftime("%Y-%m-%d")

        if(user_info == None):
            user_info = {
                "name":"User",
                "age":"unknown",
                "gender":"unknown",
                "location":"Earth"
            }

        # Replace parameters
        prompt = re.sub(r' +', ' ', prompt)
        prompt = re.sub(r'\t', ' ', prompt)
        prompt = prompt.replace("{$character.name}", self.details['Name'])
        prompt = prompt.replace("{$character.likes}", self.details['Likes'])
        prompt = prompt.replace("{$character.desires}", self.details['Desires'])
        prompt = prompt.replace("{$character.backstory}", self.details['Backstory'])
        prompt = prompt.replace("{$user.name}", user_info.get('name', ''))
        prompt = prompt.replace("{$user.age}", str(user_info.get('age', '')))
        prompt = prompt.replace("{$user.gender}", user_info.get('gender', ''))
        prompt = prompt.replace("{$date}", current_date)
        prompt = prompt.replace("{$user.location}", user_info.get('location', ''))
        prompt = prompt.replace("{$history}", chat_history)
        prompt = prompt.replace("{$chat.userprompt}", userprompt)
        prompt = prompt.replace("{$chat.summary}", chatsummary)
        prompt = prompt.replace("{$program.instructions}", self.details['PromptInstruction'])
        prompt = prompt.replace("{$innermonologue}", innermonologue)
        prompt = prompt.replace("{$timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if(self.lastBotPromptTime):
            prompt = prompt.replace("{$lastbottimestamp}", self.lastBotPromptTime.strftime("%Y-%m-%d %H:%M:%S"))
        if(self.lastUserPromptTime):
            prompt = prompt.replace("{$lastusertimestamp}", self.lastUserPromptTime.strftime("%Y-%m-%d %H:%M:%S"))

        if(self.chat_history.messages):
            m = self.chat_history.messages[len(self.chat_history.messages) - 1]
            print(type(m))
            print('last message: ' + m.content)
            prompt = prompt.replace("{$character.lastprompt}", m.content)
        else:
            prompt = prompt.replace("{$character.lastprompt}", "")
        return prompt
    

    def doImage(self):
        thoughts = '\n'.join(self.innermonologue)
        print('THOUGHTS FOR IMAGE')
        print(thoughts)

        prompt = thoughts + '\n\nBased on the context provided, create a prompt for stable diffusion to generate a image that matches the most recent statements in the transcript. Return only the prompt and nothing else and keep it very concise. The Prompt should be in the form of, description of scene, supporting descriptors. For example, "mystical dark forest, wooden box with glowing symbol, magic, fantasy"'

        print('generating prompt')
        llm = ChatbotLLM(self.config, 75)
        imagegen_prompt = llm.instruct(prompt)
        print('PROMPT:' + imagegen_prompt)
        self.send_data_to_client(imagegen_prompt, self.sid)

        print('calling generate-image')
        url = "http://localhost:8001/generate-image"
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            "prompt": imagegen_prompt + ',artstation',
            "device_type": "GPU",
            "param_dtype": "torch.float16"
        })

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                self.send_image_func(response.json()['image_url'], self.sid) 
                print(response.json()['image_url'][:50])    
            else:
                print('error in imagegen thread')
                print(response)
        except Exception as e:
            print('Error calling generate_image API')
            print(e)
        
    def update_imagegen(self):
        updating = False

        print('starting update_imagegen thread')

        while self.running:
            time.sleep(10)
            
            if(not updating):
                updating = True

                self.doImage()

                updating = False           

    def update_inner_monologue(self):
        thinking = False

        while self.running:
            # Define how often you want to update the inner monologue, e.g., every 5 seconds
            time.sleep(5)
            # Here, implement the logic to generate the inner monologue. This is a placeholder.
            # You'll need to adjust this to fit how your ChatbotLLM.doInnerMonologue works.
            # Assuming doInnerMonologue takes a system prompt and a user prompt to generate the inner monologue.
            while(self.interrupted):
                print('was interrupted. waiting 2 seconds more')
                self.interrupted = False
                time.sleep(2)

            while(self.prompting):
                time.sleep(2)

            if(not thinking):
                thinking = True
                if self.chat_history.messages:
                    llm = ChatbotLLM(self.config)
                    user_data = {"name":"Jamie", "age":45, "gender":"M", "location":"Earth"}
                    stringChatHistory = '\n'.join(map(lambda m : m.content, self.chat_history.messages))

                    llm_system_prompt = self.resolve_prompt(
                        self.details['ThinkSystemPrompt'],
                        user_data,
                        stringChatHistory,
                        '',
                        '',
                        '\n'.join(self.innermonologue)
                    )
                    llm_user_prompt = self.resolve_prompt(
                        self.details['ThinkUserPrompt'],
                        user_data,
                        stringChatHistory,
                        '',
                        '',
                        '\n'.join(self.innermonologue)
                    )
                    determineSpeakUserPrompt= self.resolve_prompt(
                        self.details['DecideThinkOrSpeak'],
                        user_data,
                        stringChatHistory,
                        '',
                        '',
                        '\n'.join(self.innermonologue)
                    )

                    # First, get the bot's most recent thought
                    try:
                        thought = llm.doInnerMonologue(llm_system_prompt, llm_user_prompt)
                        if(thought):
                            self.innermonologue.append(datetime.now().strftime("(%H:%M:%S)") + ' ' + thought["response"])        
                        if(len(self.innermonologue) > 4):
                            self.innermonologue.pop(0)
                    except:
                        print('unable to get innermonologue')
                    
                    print(self.innermonologue)

                    # Now, determine whether or not the bot should think out loud.
                    try:
                        thinkoutloud = llm.makeDecision(llm_system_prompt, determineSpeakUserPrompt)
                        decision = thinkoutloud["decision"]
                        print('decision to speak is : ' + decision)

                        if(decision == 'speak'):
                            # if here, then the chatbot has decided to speak
                            # but often the chatbot isn't really adding to the story.
                            # so let's double check with it that what it has decided to say
                            # really does move the story forward.
                            botstatement = thinkoutloud['response']
                            confirmation = llm.makeDecision('you are an amazing author. Provide an answer to the question below',  
                                                            ''.join(['The following is a section from a book that you are writing. The story is of two characters.',
                                                            'The first character is named ' + self.details['Name'] + '. Their backstory is as follows :',
                                                            self.details['Backstory'] + '.\n',
                                                            'The other character is named ' + user_data['name'] + '.',
                                                            'The section of the book you are working on now has the following transcript between these two characters :\n\n',
                                                            stringChatHistory,
                                                            '\n\n',
                                                            'You are thinking about adding the following statement from ' + self.details['Name'] + '.',
                                                            'By adding this, is the story made better? Or should it be left out?',
                                                            'It should be left out if it is mostly repeating what was just said.',
                                                            'It should be left out if it begins mostly with the same words in the last sentence.',
                                                            'It should be left out if it does not add any more progress to the story.',
                                                            'Leave it in if it adds new context or details to what ' + self.details['Name'] + ' previously said.',
                                                            'Answer with just yes, if it should be added and no if it should be left out. Be certain that it makes sense to add this new statement from ' + self.details['Name'] + '.',
                                                            'Answer should be in json format {"response":"response here"}. response can be either "yes" or "no". Be sure to reply with valid json and only valid json.']))
                            print('CONFIRMATION:')
                            print(confirmation)
                            if(confirmation['response'] == 'yes'):
                                message_timestamp = datetime.now().strftime("(%H:%M:%S)")
                                responsemessage = f"{message_timestamp} {thinkoutloud['response']}"
                                self.chat_history.add_ai_message(self.details["Name"] + ':' +  responsemessage)
                                self.lastBotPromptTime = datetime.now()
                                self.send_to_client(thinkoutloud, self.sid)

                                self.summarize()

                            else:
                                print('chatbot decided not to say it')

                            
                    except Exception as e:
                        print('unable to get decision to speak or wait')
                        print(e)
                thinking = False
                
    def stop_inner_monologue(self):
        self.running = False
        if self.inner_monologue_thread.is_alive():
            self.inner_monologue_thread.join()    
        print("inner monologue thread ended")  

    def stop_imagegen_thread(self):
        self.running = False
        if self.imagegen_thread.is_alive():
            self.imagegen_thread.join()
        print("imagegen thread ended")  

    def interrupt(self):
        self.interrupted = True