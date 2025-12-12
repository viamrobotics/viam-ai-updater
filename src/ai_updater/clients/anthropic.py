from .base import Client
import anthropic

class Antrhopic(Client):

    client: anthropic.Client

    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
