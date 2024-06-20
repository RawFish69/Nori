import requests
import time
import PyPDF2
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
API_KEY = ""


class GPTRequest:
    MODELS = ['gpt-3.5-turbo', 'text-davinci-003', 'text-babbage-001', 'text-curie-001', 'text-cushing-001', 'text-edison-002']

    def __init__(self):
        self.engine = GPTRequest.MODELS[0]
        self.all_prompt = ""
        self.all_response = ""

    def change_engine(self, index):
        if index < len(GPTRequest.MODELS):
            self.engine = GPTRequest.MODELS[index]
            logger.info(f'AI Model has switched to {self.engine}')

    def auto_reply(self, prompt: str, previous_prompt: str, previous_response: str):
        """Calls the OpenAI API endpoint, processes the output, and extracts the reply."""
        gpt_endpoint = "https://api.openai.com/v1/chat/completions"
        common_endpoint = "https://api.openai.com/v1/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        self.all_prompt += f"{prompt}\n"
        if 'gpt' in self.engine.lower():
            system_message = f"previous prompt: {previous_prompt[-2000:]}, previous response: {previous_response[-2000:]}"
            data = {
                "model": self.engine,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "assistant", "content": ""},
                    {"role": "user", "content": f"{prompt}"},
                ],
                "max_tokens": 500,
                "temperature": 0.5,
                "top_p": 1,
            }
            response = requests.post(gpt_endpoint, headers=headers, json=data)
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            self.all_response += f"{generated_text}\n"
            logger.info(f'Response: {generated_text}')
        else:
            data = {
                "model": self.engine,
                "prompt": prompt,
                "max_tokens": 400,
                "temperature": 0.5,
                "top_p": 1,
            }
            response = requests.post(common_endpoint, headers=headers, json=data)
            result = response.json()
            generated_text = result["choices"][0]["text"]
            logger.info(f'Response: {generated_text}')


class PDFReader:
    @staticmethod
    def read_pdf(file_path, max_tokens=4000):
        """限制字符有点问题，WIP"""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                text += ' ' + page_text
                if len(text.split()) > max_tokens:
                    text = ' '.join(text.split()[:max_tokens])
                    break
        return text


logger.info('Starting the application')  # Log an informational message

gpt_request = GPTRequest()
file_path_pdf = "test.pdf"
scan = PDFReader()
pdf_text = scan.read_pdf(file_path=file_path_pdf)
convo_limit = 10

for _ in range(convo_limit):
    user_prompt = pdf_text
    logger.info(f'User prompt: {user_prompt}')
    gpt_request.auto_reply(prompt=user_prompt, previous_prompt=gpt_request.all_prompt, previous_response=gpt_request.all_response)
    time.sleep(20)

logger.info('Application finished')
