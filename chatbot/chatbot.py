from datetime import datetime
import re
import threading
import time
from chatbot.chatbot_llm import ChatbotLLM
from langchain.memory import ChatMessageHistory

class Chatbot:
    def __init__(self, send_response_func, sid, socketio, config):
        print(config)
        self.send_to_client = send_response_func
        self.message_history=""
        self.config = config
        self.chat_history = ChatMessageHistory()
        self.innermonologue = []
        self.running = True
        self.details = {}  # Assuming this gets loaded later
        self.socketio = socketio
        self.sid = sid

    def startThinkingThread(self):
        # Start the inner monologue thread
        self.inner_monologue_thread = threading.Thread(target=self.update_inner_monologue)
        self.inner_monologue_thread.start()

    def process_message(self, message):        
        response = f"Chatbot received message: {message}"
        user_data = {"name":"Jamie", "age":45, "gender":"M", "location":"Earth"}
        message_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            llm = ChatbotLLM(self.config)
            response = llm.doPrompt(llm_system_prompt, llm_user_prompt)

            message_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            responsemessage = f"{message_timestamp} {response['response']}"
            self.chat_history.add_ai_message(self.details["Name"] + ':' +  responsemessage)

            self.send_to_client(response, self.sid)
            
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
        
        return prompt
    
    def update_inner_monologue(self):
        while self.running:
            # Define how often you want to update the inner monologue, e.g., every 5 seconds
            time.sleep(5)
            # Here, implement the logic to generate the inner monologue. This is a placeholder.
            # You'll need to adjust this to fit how your ChatbotLLM.doInnerMonologue works.
            # Assuming doInnerMonologue takes a system prompt and a user prompt to generate the inner monologue.
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
                        self.innermonologue.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' ' + thought["response"])        
                    if(len(self.innermonologue) > 10):
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
                        message_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        responsemessage = f"{message_timestamp} {thinkoutloud['response']}"
                        self.chat_history.add_ai_message(self.details["Name"] + ':' +  responsemessage)

                        self.send_to_client(thinkoutloud, self.sid)

                        
                except Exception as e:
                    print('unable to get decision to speak or wait')
                    print(e)

    def stop_inner_monologue(self):
        self.running = False
        if self.inner_monologue_thread.is_alive():
            self.inner_monologue_thread.join()    