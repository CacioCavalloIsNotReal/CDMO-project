# Usa un'immagine base (ad esempio, una versione di Python)
FROM python:3.9

# Imposta la directory di lavoro
RUN mkdir cdmo
WORKDIR /cdmo

# Copia i file necessari nella directory di lavoro
ADD . .

# Installa le dipendenze

# important bec in intstall the driver
RUN apt-get update && apt-get install -y minizinc 

RUN pip install -r requirements.txt

# Comando per eseguire l'applicazione
CMD ["python", "CP/main.py"]
# docker build -t cdmo-proj-image .
# docker run -it --rm -v /home/francesco/Scrivania/CDMO/CDMO-proj/CDMO-project/:/cdmo cdmo-proj-image
