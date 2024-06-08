from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Função para verificar se o email começa com algum dos prefixos indesejados
def email_invalid(email):
    if pd.isna(email):
        return True
    prefixes = ["cliente", "nao", "teste", "ooo", "aaa", "sss", "semem", "pacie", "0@", "00@", "000@", "0000@"]
    return any(email.lower().startswith(prefix) for prefix in prefixes)

# Função para extrair o primeiro nome e capitalizar a primeira letra
def extract_first_name(full_name):
    if pd.isna(full_name):
        return ''
    first_name = full_name.split()[0]
    return first_name.capitalize()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    if file:
        # Salvar o arquivo no servidor
        filename = secure_filename(file.filename)
        temp_file_path = os.path.join('uploads', filename)
        file.save(temp_file_path)
        
        # Ler o CSV
        df = pd.read_csv(temp_file_path)
        
        # Colunas a serem excluídas
        columns_to_drop = [
            "DiaCompra", "MesCompra", "AnoCompra", "CPF", "TelCelPaciente",
            "DataNascimento", "CidadePaciente", "EndPaciente", "EstadoPaciente",
            "Unidade", "Procedimento Grupo", "Procedimento", "Origem", "ValorCompra"
        ]
        
        # Remover as colunas especificadas
        df = df.drop(columns=columns_to_drop, errors='ignore')
        
        # Remover linhas onde a coluna EmailPaciente está vazia ou começa com os prefixos indesejados
        df = df[~df['EmailPaciente'].apply(email_invalid)]
        
        # Remover linhas duplicadas na coluna EmailPaciente
        df = df.drop_duplicates(subset='EmailPaciente', keep='first')
        
        # Renomear as colunas
        df = df.rename(columns={
            "Paciente": "Name",
            "EmailPaciente": "EmailAddress",
            "Marca": "InterestBrand",
            "DataOrcamento": "Date"
        })
        
        # Criar a nova coluna 'FirstName' com o primeiro nome capitalizado
        df.insert(1, 'FirstName', df['Name'].apply(extract_first_name))
        
        # Salvar a planilha modificada como CSV em um local temporário
        output_file_path = os.path.join('uploads', 'processed_file.csv')
        df.to_csv(output_file_path, index=False)
        
        # Remover o arquivo temporário original
        os.remove(temp_file_path)
        
        return send_file(output_file_path, as_attachment=True, download_name='processed_file.csv', mimetype='text/csv')

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
