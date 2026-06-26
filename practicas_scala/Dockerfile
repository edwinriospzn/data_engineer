FROM jupyter/all-spark-notebook:spark-3.4.0

# Instalar Java 11
USER root
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    update-alternatives --set java /usr/lib/jvm/java-11-openjdk-amd64/bin/java && \
    rm -rf /var/lib/apt/lists/*

# Configurar Java 11 como predeterminado
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

USER jovyan

# Instalar coursier
RUN mkdir -p /home/jovyan/.local/bin && \
    curl -Lo /home/jovyan/.local/bin/coursier https://git.io/coursier-cli && \
    chmod +x /home/jovyan/.local/bin/coursier

# Instalar Almond
RUN export PATH=/home/jovyan/.local/bin:$PATH && \
    /home/jovyan/.local/bin/coursier launch almond:0.13.3 -- --install

# Copiar la configuración del kernel
COPY docker/kernel/kernel.json /home/jovyan/.local/share/jupyter/kernels/scala/kernel.json

WORKDIR /home/jovyan

EXPOSE 8888 4040
