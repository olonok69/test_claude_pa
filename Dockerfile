FROM ollama/ollama

WORKDIR /root

COPY requirements.txt ./

RUN apt update 
RUN apt-get install -y python3 python3-pip vim git
RUN pip install -r requirements.txt

EXPOSE 8510
EXPOSE 11434
ENTRYPOINT ["./entrypoint.sh"]

