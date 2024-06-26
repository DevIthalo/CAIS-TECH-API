from flask import Flask, Response
import os.path
import os
import random
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask_cors import CORS 
from flask import request
app = Flask(__name__)
CORS(app)  

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# ID da planilha do google sheets
SAMPLE_SPREADSHEET_ID = '1pnHQVTETTnWnOtyz0o0InjNoW2nvQbHKDs0ya4Zqm4s'
# Página da planilha e  intervalos de células a serem lidas
SAMPLE_RANGE_NAME = 'Respostas ao formulário 1!C2:G680'

# Obtém o caminho absoluto para o diretório do script
script_directory = os.path.dirname(os.path.abspath(__file__))
token_file_path = os.path.join(script_directory, 'token.json')

# Função para execução do sorteio
def get_random_row(valor_pesquisa):
    creds = None
    # Verifica se o token existe
    if os.path.exists(token_file_path):
        creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)

    # Caso o token não existir ou esteja inválido é solicitada a autenticação do google
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])
        if not values:
            return None

        for row in values:
            # print("Comparando:", int(row[3]), "com:", valor_pesquisa)
            if int(row[3]) == valor_pesquisa:
                return {
                    'vendedor': row[0],
                    'cliente': row[1],
                    'telefone': row[2], 
                    'ponto': row[3],
                }

        return None

    except HttpError as err:
        print(err)
        return None


@app.route('/', methods=['POST'])
def index():
    # Obtém o JSON do corpo da requisição
    request_data = request.json
    random_data = get_random_row(request_data['result'])
    
    if random_data:
        # Serializa os dados em JSON usando o módulo json
        print(random_data)
        json_data = json.dumps(random_data, ensure_ascii=False)
        response = Response(json_data, content_type='application/json;')
        return response
    else:
        return Response(json.dumps({"error": "O ponto sorteado não possui registro de venda."}), content_type='application/json');

if __name__ == '__main__':
    app.run(debug=True)