import xml.etree.ElementTree as ET
from datetime import datetime
import re


class Character:
    def __init__(self, name, gender, system_prompts, user_prompts, response_instruction, waiting_instruction, animations):
        self.name = name
        self.gender = gender
        self.prompts = Prompt(system_prompts, user_prompts, response_instruction, waiting_instruction, animations)
    
    @classmethod
    def load_from_xml(cls, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        name = root.attrib.get('name', '')
        gender = root.attrib.get('gender', '')
        system_prompts = ""
        user_prompts = ""
        response_instruction = ""
        waiting_instruction = ""

        for prompts in root.find('Prompts'):
            if prompts.tag == "System":
                system_prompts = prompts.text.strip()
            elif prompts.tag == "User":
                user_prompts = prompts.text.strip()

        for inst in root.find('Instructions'):
            if inst.tag == "Instruction" and inst.attrib.get('type','') == 'response':
                response_instruction = inst.text.strip()
            elif inst.tag == "Instruction" and inst.attrib.get('type','') == 'waiting':
                waiting_instruction = inst.text.strip()

        animationslist = '[]'
        animationsnode = root.find('Animations')
        if(not animationsnode == None):
            animationslist = [item.strip() for item in animationsnode.text.strip().split(',')]


            
        return cls(name, gender, system_prompts, user_prompts, response_instruction, waiting_instruction, animationslist)

    def getinfo(self):
        return {"name":self.name, "gender":self.gender}
    
class Prompt:
    def __init__(self, system_prompt, user_prompt, response_instruction, waiting_instruction, animations):
        print('Creating Prompt object')

        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.response_instruction = response_instruction
        self.waiting_instruction = waiting_instruction
        self.animations = animations

        print('\n\nsystem_prompt:' + self.system_prompt)
        print('\n\nuser_prompt:' + self.user_prompt)
        print('\n\nresponse_instruction:' + self.response_instruction)
        print('\n\nwaiting_instruction:' + self.waiting_instruction)
        print('\n\n>>> SYSTEM PROMPT <<<\n' + self.resolve_prompt("system", None, None, 'this is the chat history', 'this is the user prompt', "waiting"))
        print('\n\n>>> USER RESPONSE PROMPT <<<\n' + self.resolve_prompt("user", None, None, 'this is the chat history', 'this is the user prompt', "response"))
        print('\n\n>>> USER WAITING PROMPT <<<\n' + self.resolve_prompt("user", None, None, 'this is the chat history', 'this is the user prompt', "waiting"))

    def resolve_prompt(self, prompt_type, user_info, character_info, chat_history, chat_summary, user_prompt, botstate="response"):
        if prompt_type == "system":
            prompt = self.system_prompt
        elif prompt_type == "user":
            prompt = self.user_prompt
        else:
            raise ValueError("Invalid prompt type")
        
        if(botstate == "waiting"):
            prompt = prompt.replace("{$program.instructions}", self.waiting_instruction)
        else:
            prompt = prompt.replace("{$program.instructions}", self.response_instruction)

        returnPrompt = PromptResolver.resolve(user_info=user_info, 
                                              character_info=character_info, 
                                              prompt=prompt, 
                                              userprompt=user_prompt, 
                                              chat_history=chat_history, 
                                              chatsummary=chat_summary,
                                              animationFiles=self.animations, 
                                              botstate=botstate)

        return returnPrompt


class PromptResolver:
    @classmethod
    def resolve(cls, user_info=None, character_info=None, prompt="", userprompt="", chat_history="", chatsummary="", animationFiles=[], botstate="response"):
                # Current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        if(user_info == None):
            user_info = {
                "name":"User",
                "age":"unknown",
                "gender":"unknown",
                "location":"Earth"
            }

        if(character_info == None):
            character_info = {
                "name":"Chatbot",                
            }

        # Replace parameters
        prompt = re.sub(r' +', ' ', prompt)
        prompt = prompt.replace("{$character.name}", character_info.get('name', ''))
        prompt = prompt.replace("{$user.name}", user_info.get('name', ''))
        prompt = prompt.replace("{$user.age}", str(user_info.get('age', '')))
        prompt = prompt.replace("{$user.gender}", user_info.get('gender', ''))
        prompt = prompt.replace("{$date}", current_date)
        prompt = prompt.replace("{$user.location}", user_info.get('location', ''))
        prompt = prompt.replace("{$history}", chat_history)
        prompt = prompt.replace("{$chat.userprompt}", userprompt)
        prompt = prompt.replace("{$chat.summary}", chatsummary)
        animationFilesStr = ''
        if(len(animationFiles)>0):
            animationFilesStr = str(animationFiles)
            prompt = prompt.replace("{$animationfiles}", animationFilesStr)
        
        return prompt