import os
import yaml
import json
import requests
from termcolor import colored
from prompts import planning_agent_prompt, integration_agent_prompt

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        for key, value in config.items():
            os.environ[key] = value

class Agent:
    def __init__(self, model, tool, temperature=0, max_tokens=5000, planning_agent_prompt=None, integration_agent_prompt=None, verbose=False):
        load_config('config.yaml')
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tool = tool
        self.tool_specs = tool.__doc__
        self.planning_agent_prompt = planning_agent_prompt
        self.integration_agent_prompt = integration_agent_prompt
        self.model = model
        self.verbose = verbose

    def run_integration_agent(self, query, outputs=None, plan=None, feedback=None):

        system_prompt = self.integration_agent_prompt.format(
            outputs=outputs,
            plan=plan,
            feedback=feedback,
            tool_specs=self.tool_specs
        )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        json_data = json.dumps(data)
        try:
            response = requests.post(self.url, headers=self.headers, data=json_data, timeout=180)
            response_dict = response.json()

            content = self.check_response(response_dict)
            if content:
                if self.verbose:
                    print(colored(f"Integration Agent: {content}", 'green'))
                return content
        except Exception as e:
            print(colored(f"Exception occurred: {e}", 'red'))
            return None

    def run_planning_agent(self, query, plan=None, outputs=None, feedback=None):

        system_prompt = self.planning_agent_prompt.format(
            outputs=outputs,
            plan=plan,
            feedback=feedback,
            tool_specs=self.tool_specs
        )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        json_data = json.dumps(data)
        try:
            response = requests.post(self.url, headers=self.headers, data=json_data, timeout=180)
            response_dict = response.json()

            content = self.check_response(response_dict)
            if content:
                if self.verbose:
                    print(colored(f"Planning Agent: {content}", 'green'))
                return content
        except Exception as e:
            print(colored(f"Exception occurred: {e}", 'red'))
            return None

    def check_response(self, response_dict):
        if 'choices' in response_dict and len(response_dict['choices']) > 0:
            return response_dict['choices'][0]['message']['content']
        else:
            print(colored(f"Error: 'choices' field missing in response. Full response: {response_dict}", 'red'))
            return None
