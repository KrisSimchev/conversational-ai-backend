import json
import os
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from config import Config

secret_key = Config.SECRET_KEY

def create_assistant(client):
  assistant_file_path = 'assistant.json'

  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
  else:
    file = client.files.create(file=open("knowledge.docx", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(instructions="""
          The assistant has been programmed to be the best customer support chatbot.
          A document has been provided with the information needed for answers.
          Respond in Bulgarian all the time!
          """,
                                              model="gpt-4-1106-preview",
                                              tools=[{
                                                  "type": "retrieval"
                                              }],
                                              file_ids=[file.id])

    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)

    assistant_id = assistant.id

  return assistant_id

def generate_token(user_id):
    s = Serializer(secret_key, expires_in=3600) 
    token = s.dumps({'user_id': user_id}).decode('utf-8')
    return token

def validate_token(token):
    s = Serializer(secret_key)

    try:
        data = s.loads(token)
        return data['user_id']
    except:
        return None
