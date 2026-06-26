# 1. Base image
FROM centos:7

# PARCHE DEFINITIVO PARA REPOS DE CENTOS 7 (EOL)
RUN rm -vf /etc/yum.repos.d/*.repo && \
    echo -e "[base]\nname=CentOS-7 - Base - vault.centos.org\nbaseurl=http://vault.centos.org/7.9.2009/os/x86_64/\ngpgcheck=1\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7\nenabled=1\n\n[updates]\nname=CentOS-7 - Updates - vault.centos.org\nbaseurl=http://vault.centos.org/7.9.2009/updates/x86_64/\ngpgcheck=1\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7\nenabled=1" > /etc/yum.repos.d/CentOS-Vault.repo

# 5. Label requirement
LABEL owner="s4ncampus"

# 2. Environment variable and directory creation
ENV VIRTUALHOST_FOLDER=/var/sites/awesomesite/
RUN mkdir -p $VIRTUALHOST_FOLDER

# 8. Install Python 2
RUN yum install -y python && yum clean all

# 6. Configure user and directory permissions
RUN useradd -m dockeruser && \
    chown -R dockeruser:dockeruser $VIRTUALHOST_FOLDER

# 3. Volume requirement
VOLUME vol1

# 4. Expose port 9999
EXPOSE 9999

# 7. Copy and prepare entrypoint script
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

# 6a & 6b. Move to user home directory and touch temp file
WORKDIR /home/dockeruser
USER dockeruser
RUN touch temp

# 7a. Set up the entrypoint execution
ENTRYPOINT ["bash", "/entrypoint.sh"]
