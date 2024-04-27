from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from shared_resources import client_sessions
import re
import threading
import json

class ChatbotLLM:
    def __init__(self, config, max_tokens=300):
        self.message_history=""
        self.config = config
        print('CONFIGDATA!!!!')
        print(config['OPENAI_CHAT_MODEL'])
        
        self.chat_model = ChatOpenAI(
            base_url=config["OPENAIAPI_CHAT_BASEURL"],
            model_name=config["OPENAI_CHAT_MODEL"],
            api_key=config["OPENAIAPI_CHAT_KEY"], verbose=True, max_tokens=max_tokens)



    def runLLM(self, systemprompt, userprompt):
        """Runs the LLM Prompt and returns extracted JSON from the result.
            - Note : this should handle OpenAI compatible API but I'd also like
                to be able to handle Koboldcpp API, and not sure if it would be 
                best to use LangChain for it, given the nuanced approach that Kobold
                takes.
        ----------        
        """
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
        return extractedJSONResponse



    def doPrompt(self, systemprompt, userprompt):
        """Handles user prompt.
        ----------        
        """        
        extractedJSONResponse = self.runLLM(systemprompt, userprompt)
        counter = 0
        while(extractedJSONResponse == None and counter < 3):
            extractedJSONResponse = self.runLLM(systemprompt, userprompt)
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
        """Handles the inner-monologue
            This is actually just the same as doPrompt for now
        ----------        
        """        
        extractedJSONResponse = self.doPrompt(systemprompt, userprompt)        
        return extractedJSONResponse



    def makeDecision(self, systemprompt, userprompt):
        """Handles decision making
           This is actually just the same as doPrompt for now
        ----------        
        """            
        extractedJSONResponse = self.doPrompt(systemprompt, userprompt)        
        return extractedJSONResponse



    def instruct(self, userprompt):
        sys_prompt = 'Below is an instruction that describes a task. Write a response that appropriately completes the request.'        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    sys_prompt
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | self.chat_model
        resp = chain.invoke({"messages": [userprompt]})        
        return resp.content
    
    def extract_json_from_markdown(self, markdown_str, counter = 0):
        """Extracts JSON content from the LLM response
           Or, maybe it is better phrased as this function tries to extract
           the JSON from the response. 
           Sometimes the LLM just won't play nice.
        ----------        
        """               
        # Regular expression to find code blocks that might contain JSON
        code_block_pattern = r"{.*}"
        
        print('in extract_json')
        print(markdown_str)
        markdown_str = str(markdown_str).replace("\n", "")
        markdown_str = re.sub(r"\(\d{2}:\d{2}:\d{2}\)", "", markdown_str)

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
