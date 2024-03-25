import xml.etree.ElementTree as ET
from datetime import datetime
import re


class Character:
    def __init__(self, name, gender, system_prompts, user_prompts):
        self.name = name
        self.gender = gender
        self.prompts = Prompt(system_prompts, user_prompts)

    @classmethod
    def load_from_xml(cls, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        name = root.attrib.get('name', '')
        gender = root.attrib.get('gender', '')
        system_prompts = ""
        user_prompts = ""

        for prompts in root.find('Prompts'):
            if prompts.tag == "System":
                system_prompts = prompts.text.strip()
            elif prompts.tag == "User":
                user_prompts = prompts.text.strip()

        return cls(name, gender, system_prompts, user_prompts)

class Prompt:
    def __init__(self, system_prompt, user_prompt):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def resolve_prompt(self, prompt_type, user_info, chat_history, user_prompt):
        if prompt_type == "system":
            prompt = self.system_prompt
        elif prompt_type == "user":
            prompt = self.user_prompt
        else:
            raise ValueError("Invalid prompt type")

        # Current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Replace parameters
        prompt = re.sub(r' +', ' ', prompt)
        prompt = prompt.replace("{$character.name}", user_info.get('character_name', ''))
        prompt = prompt.replace("{$user.name}", user_info.get('name', ''))
        prompt = prompt.replace("{$user.age}", str(user_info.get('age', '')))
        prompt = prompt.replace("{$user.gender}", user_info.get('gender', ''))
        prompt = prompt.replace("{$date}", current_date)
        prompt = prompt.replace("{$user.location}", user_info.get('location', ''))
        prompt = prompt.replace("{$history}", chat_history)
        prompt = prompt.replace("{$chat.userprompt}", user_prompt)

        return prompt