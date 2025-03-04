# Usa un'immagine base (ad esempio, una versione di Python)
FROM python:3.9

# Imposta la directory di lavoro
RUN mkdir cdmo
WORKDIR /cdmo

# Copia i file necessari nella directory di lavoro
ADD . .

# Installa le dipendenze
RUN apt-get update && apt-get install -y minizinc

RUN pip install -r requirements.txt

# Comando per eseguire l'applicazione
CMD ["python", "app.py"]
# docker run -it --rm -v /home/francesco/Scrivania/CDMO-proj/CDMO-project/:/cdmo cdmo-proj-image