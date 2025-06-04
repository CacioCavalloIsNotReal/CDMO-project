FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update
RUN apt-get install -y tzdata
RUN apt-get install -y wget

RUN apt-get install -y python3-pip
RUN apt-get install -y libgl1-mesa-dev
RUN apt-get install -y libglib2.0-0
RUN apt-get update && apt-get install -y libqt5printsupport5
RUN apt-get install -y nano

RUN ln -s /usr/bin/python3 /usr/bin/python

# Set the working directory
RUN mkdir /home/cdmo
WORKDIR /home/cdmo

# Copy all the necessary files to the working directory
ADD . .

# python packages
RUN python3 -m pip install -r requirements.txt

# MiniZinc
ARG MINIZINC_VERSION=2.6.2
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/$MINIZINC_VERSION/MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
RUN tar -xvf MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64.tgz
# Move MiniZinc in an easier to access location
RUN mv MiniZincIDE-$MINIZINC_VERSION-bundle-linux-x86_64 /opt/minizinc

# HIGhS
RUN mkdir /opt/highs
RUN wget https://github.com/JuliaBinaryWrappers/HiGHSstatic_jll.jl/releases/download/HiGHSstatic-v1.10.0%2B0/HiGHSstatic.v1.10.0.x86_64-linux-gnu-cxx11.tar.gz
# Move HIGhS in an easier to access location
RUN tar -xvzf HiGHSstatic.v1.10.0.x86_64-linux-gnu-cxx11.tar.gz -C /opt/highs

# Gurobi
ENV GUROBI_VERSION=12.0.1
COPY gurobi.lic /opt/gurobi1201/gurobi.lic
RUN wget https://packages.gurobi.com/12.0/gurobi12.0.1_linux64.tar.gz
RUN tar -xvzf gurobi12.0.1_linux64.tar.gz -C /opt


# Add minizinc and highs to PATH
ENV PATH="/opt/minizinc/bin:$PATH"
ENV PATH="/opt/highs/bin:$PATH"
ENV PATH="/opt/gurobi1201/linux64/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/gurobi1201/linux64/lib:$LD_LIBRARY_PATH"
ENV GRB_LICENSE_FILE="/opt/gurobi1201/gurobi.lic"

# Verify installation
RUN minizinc --version
RUN highs --version

CMD ["python", "app.py"]

# Commands to run
# docker build -t cdmo-project .
# docker run -it cdmo-project bash
# docker run -it --rm -v /home/francesco/Scrivania/CDMO/repo/CDMO-project/:/cdmo cdmo-proj-image
# docker run -it --rm -v /home/francesco/Scrivania/CDMO/repo/CDMO-project/:/cdmo cdmo-project bash