# Usa un'immagine base (ad esempio, una versione di Python)
FROM python:3.9

# Imposta la directory di lavoro
RUN mkdir cdmo
WORKDIR /cdmo

# Copia i file necessari nella directory di lavoro
ADD . .

# Installa le dipendenze

ARG MINIZINC_VERSION=2.9.2

# Install MiniZinc
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/$MINIZINC_VERSION/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
WORKDIR "/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/bin"

# ENV PATH="${PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/bin"
# ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/lib"
# ENV QT_PLUGIN_PATH="${QT_PLUGIN_PATH}:/cdmo/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64/plugins"


# important bec in intstall the driver
# RUN apt-get update && apt-get install -y minizinc=2.6.4+dfsg1-1
# RUN apt-get update && apt-get install -y minizinc=2.9.2+dfsg1-1

RUN pip install -r requirements.txt

# Comando per eseguire l'applicazione
CMD ["python", "CP/main.py"]
# docker build -t cdmo-proj-image .
# per entrare nella bash del container
# docker run -it cdmo-proj-image bash

# docker run -it --rm -v /home/francesco/Scrivania/CDMO/CDMO-proj/CDMO-project/:/cdmo cdmo-proj-image
