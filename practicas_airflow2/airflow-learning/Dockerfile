FROM apache/airflow:2.10.3

USER root

# Install Java (required for PySpark)
RUN apt-get update -qq && \
    apt-get install -y -qq openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=${JAVA_HOME}/bin:${PATH}

# Switch to airflow user and install PySpark
USER airflow
RUN pip install --no-cache-dir pyspark pandas

# Keep the same user
USER airflow