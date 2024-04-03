import json

class Config:
    """Base configuration class."""
    # Default values can be set here

    @staticmethod
    def load_config(file_path='config.json'):
        """Load configuration from a JSON file."""
        with open(file_path, 'r') as config_file:
            config_data = json.load(config_file)
        print('config loaded')
        print(config_data)
        return config_data

# Load configurations dynamically from config.json
configurations = Config.load_config()

# For ease of use, you can directly access configurations as attributes
class DevelopmentConfig:
    DEBUG = configurations.get('DEBUG', True)
    TTS_SERVER_URL = configurations.get('TTS_SERVER_URL', 'ws://127.0.0.1:8000/audio_stream')
    SECRET_KEY = configurations.get('SECRET_KEY', 'your_secret_key_here')
    SOLAR_KEY = configurations.get('SOLAR_KEY', '')
    SOLAR_BASEURL = configurations.get('SOLAR_BASEURL', '')
    SOLAR_MODEL_NAME = configurations.get('SOLAR_MODEL_NAME','solar-1-mini-chat')
    OPENAIAPI_CHAT_BASEURL = configurations.get('OPENAIAPI_CHAT_BASEURL','http://localhost:1234/v1')
    OPENAIAPI_CHAT_KEY = configurations.get('OPENAIAPI_CHAT_KEY','notneeded')
    OPENAI_CHAT_MODEL = configurations.get('OPENAI_CHAT_MODEL','test.gguf')
    THINK_FREQUENCY_SECONDS = configurations.get('THINK_FREQUENCY_SECONDS',10)
    DEFAULT_CHARACTER = configurations.get('DEFAULT_CHARACTER','./characters/aria.xml')
    CHARACTER_PATH = configurations.get('CHARACTER_PATH','./characters')

class ProductionConfig:
    DEBUG = configurations.get('DEBUG', False)
    TTS_SERVER_URL = configurations.get('TTS_SERVER_URL', 'ws://127.0.0.1:8000/audio_stream')
    SECRET_KEY = configurations.get('SECRET_KEY', 'your_secret_key_here')
    SOLAR_KEY = configurations.get('SOLAR_KEY', '')
    SOLAR_BASEURL = configurations.get('SOLAR_BASEURL', '')
    SOLAR_MODEL_NAME = configurations.get('SOLAR_MODEL_NAME','solar-1-mini-chat')
    OPENAIAPI_CHAT_BASEURL = configurations.get('OPENAIAPI_CHAT_BASEURL','http://localhost:1234/v1')
    OPENAIAPI_CHAT_KEY = configurations.get('OPENAIAPI_CHAT_KEY','notneeded')
    OPENAI_CHAT_MODEL = configurations.get('OPENAI_CHAT_MODEL','test.gguf')
    THINK_FREQUENCY_SECONDS = configurations.get('THINK_FREQUENCY_SECONDS',10)
    DEFAULT_CHARACTER = configurations.get('DEFAULT_CHARACTER','./characters/aria.xml')
    CHARACTER_PATH = configurations.get('CHARACTER_PATH','./characters')
    # Override or add any production-specific settings here based on the loaded configurations
