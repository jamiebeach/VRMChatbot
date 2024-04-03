from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from shared_resources import client_sessions
import re
import threading
import json

class ChatbotLLM:
    def __init__(self, config):
        self.message_history=""
        self.config = config
        print('CONFIGDATA!!!!')
        print(config['OPENAI_CHAT_MODEL'])
        self.chat_model = ChatOpenAI(
            base_url=config["OPENAIAPI_CHAT_BASEURL"],
            model_name=config["OPENAI_CHAT_MODEL"],
            api_key=config["OPENAIAPI_CHAT_KEY"], verbose=True)

    def doPrompt(self, systemprompt, userprompt):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    systemprompt
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | self.chat_model

        response = chain.invoke({"messages": [userprompt]})

        extractedJSONResponse = self.extract_json_from_markdown(response.content)
        counter = 0
        while(extractedJSONResponse == None and counter < 3):
            response = chain.invoke({"messages": [userprompt]})
            extractedJSONResponse = self.extract_json_from_markdown(response.content) 
            counter = counter + 1

        if(extractedJSONResponse == None):
            extractedJSONResponse = {"response":"Error", "mood":"sad"}

        print('extracted JSON:' + str(extractedJSONResponse))
            
        if(extractedJSONResponse.get('mood')):
            print('returned mood:' + extractedJSONResponse['mood'])
        else:
            print('no mood found in response. Setting to talking')
            extractedJSONResponse['mood'] = 'talking'
        
        return extractedJSONResponse

    def doInnerMonologue(self, systemprompt, userprompt):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    systemprompt
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | self.chat_model

        response = chain.invoke({"messages": [userprompt]})

        extractedJSONResponse = self.extract_json_from_markdown(response.content)
        counter = 0
        while(extractedJSONResponse == None and counter < 3):
            response = chain.invoke({"messages": [userprompt]})
            extractedJSONResponse = self.extract_json_from_markdown(response.content) 
            counter = counter + 1

        if(extractedJSONResponse == None):
            extractedJSONResponse = {"response":"Error", "mood":"sad"}

        print('extracted JSON:' + str(extractedJSONResponse))
            
        if(extractedJSONResponse.get('mood')):
            print('returned mood:' + extractedJSONResponse['mood'])
        else:
            print('no mood found in response. Setting to talking')
            extractedJSONResponse['mood'] = 'talking'
        
        return extractedJSONResponse

    def makeDecision(self, systemprompt, userprompt):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    systemprompt
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | self.chat_model

        response = chain.invoke({"messages": [userprompt]})

        extractedJSONResponse = self.extract_json_from_markdown(response.content)
        counter = 0
        while(extractedJSONResponse == None and counter < 3):
            response = chain.invoke({"messages": [userprompt]})
            extractedJSONResponse = self.extract_json_from_markdown(response.content) 
            counter = counter + 1

        if(extractedJSONResponse.get('mood')):
            print('returned mood:' + extractedJSONResponse['mood'])
        else:
            print('no mood found in response. Setting to talking')
            extractedJSONResponse['mood'] = 'talking'
            
        if(extractedJSONResponse == None):
            extractedJSONResponse = {"response":"Error"}

        print('extracted JSON:' + str(extractedJSONResponse))
                    
        return extractedJSONResponse
    
    def extract_json_from_markdown(self, markdown_str, counter = 0):
        # Regular expression to find code blocks that might contain JSON
        code_block_pattern = r"{.*}"
        
        print('in extract_json')
        print(markdown_str)
        markdown_str = str(markdown_str).replace("\n", "")

        # Search for JSON within code blocks
        matches = re.findall(code_block_pattern, markdown_str, re.DOTALL)
        
        if matches:
            # Assuming the first match is the JSON you want
            json_str = matches[0]
            
            try:
                # Parse the JSON string into a Python object
                print(json_str)
                json_data = json.loads(json_str)
                return json_data
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")

                if(counter >= 1):
                    print('not working after attempt to fix. Return none')
                    return None
                else :
                    # Let's call the chatbot again to fix the JSON
                    print('JSON Was invalid... Asking llm to fix it')
                    #response = self.chain.invoke({"messages": ['Please respond with a valid and fixed version of the following JSON: ' + json_str]})
                    #return self.extract_json_from_markdown(response.content, counter + 1)
                    return None
        else:
            print("No JSON found in Markdown.")
        
        return None
