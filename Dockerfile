# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos necessários
COPY . .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta 5000 (porta padrão do Flask)
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]