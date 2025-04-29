FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update
RUN apt-get install -y tzdata
RUN apt-get install -y wget

RUN apt-get install -y python3-pip
RUN apt-get install -y libgl1-mesa-dev
RUN apt-get install -y libglib2.0-0
RUN apt-get install -y nano
# set python3 env variable
RUN ln -s /usr/bin/python3 /usr/bin/python

# Imposta la directory di lavoro
RUN mkdir cdmo
WORKDIR /cdmo

# Copia i file necessari nella directory di lavoro
ADD . .

# python packages
RUN python3 -m pip install -r requirements.txt

# minizinc
ARG MINIZINC_VERSION=2.6.2

RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/$MINIZINC_VERSION/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz

# Sposta MiniZinc in una cartella più accessibile
RUN mv MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64 /opt/minizinc

# Aggiungi MiniZinc al PATH e imposta le variabili d'ambiente
ENV PATH="/opt/minizinc/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/minizinc/lib:${LD_LIBRARY_PATH:-}"

# Verifica l'installazione di MiniZinc
RUN minizinc --version

CMD ["python", "app.py"]