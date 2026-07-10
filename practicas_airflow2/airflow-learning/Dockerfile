FROM apache/airflow:2.10.3

USER root

# Install Java and Spark
RUN apt-get update -qq && \
    apt-get install -y -qq wget openjdk-17-jre-headless && \
    wget -q https://archive.apache.org/dist/spark/spark-3.5.4/spark-3.5.4-bin-hadoop3.tgz && \
    tar -xzf spark-3.5.4-bin-hadoop3.tgz -C /opt/ && \
    mv /opt/spark-3.5.4-bin-hadoop3 /opt/spark && \
    rm spark-3.5.4-bin-hadoop3.tgz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set permissions
RUN chown -R airflow:airflow /opt/spark

USER airflow

# Set environment variables
ENV SPARK_HOME=/opt/spark
ENV PATH=/opt/spark/bin:${PATH}
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64