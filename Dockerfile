FROM python:3.12-alpine

WORKDIR .
COPY requirements.txt requirements.txt

# install access to SQLServer
RUN apk update
RUN apk add curl
RUN apk add make
RUN apk add gcc
RUN apk add g++
RUN curl -O https://download.microsoft.com/download/1/f/f/1fffb537-26ab-4947-a46a-7a45c27f6f77/msodbcsql18_18.2.2.1-1_amd64.apk && \
    curl -O https://download.microsoft.com/download/1/f/f/1fffb537-26ab-4947-a46a-7a45c27f6f77/mssql-tools18_18.2.1.1-1_amd64.apk && \
    apk add --allow-untrusted msodbcsql18_18.2.2.1-1_amd64.apk && \
    apk add --allow-untrusted mssql-tools18_18.2.1.1-1_amd64.apk
RUN apk add unixodbc-dev
ENV PATH="$PATH:/opt/mssql-tools/bin"

RUN pip install --upgrade pip

RUN pip install -r requirements.txt
COPY . .

ENV FLASK_APP=app_main.py
ENV TZ=America/Sao_Paulo

ENV PYDB_LOGGING_FILE_MODE=a
ENV PYDB_LOGGING_FILE_PATH=/tmp/pydbref.log
ENV PYDB_LOGGING_LEVEL=debug

EXPOSE 5000
CMD ["python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000"]
