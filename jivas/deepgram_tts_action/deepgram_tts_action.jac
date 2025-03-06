import:py logging;
import:py traceback;
import:py requests;
import:py from logging { Logger }
import:jac from jivas.agent.action.tts_action { TTSAction }

node DeepgramTTSAction :TTSAction: {
    # A speech action which integrates with the Deepgram speech to text and text to speech API.

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has model:str = "aura-asteria-en"; 
    has api_key:str = "";
    
    can invoke(text:str, as_base64:bool=False, as_url:bool=False) {
        # """
        # Convert text to speech and save the audio file.

        # :param text: Text to convert to speech
        # :param as_base64: outputs audio file as base64 encoded string
        # :param as_url: outputs URL for downloading audio file
        # :return: URL to the saved audio file or base64 encoded string
        # """

        audio = None;

        # Prepare the headers with the API key
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        };

        # Prepare the payload with the text
        data = {"text": text};

        # Make the POST request to Deepgram API
        try {
            response = requests.post(
                "https://api.deepgram.com/v1/speak",
                headers=headers, 
                json=data, 
                params= {
                    'model':self.model
                }
            );
            response.raise_for_status();  # Raise an error for bad responses
            audio = response.content;

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return self.get_audio_as(audio, as_base64, as_url);
    }

}