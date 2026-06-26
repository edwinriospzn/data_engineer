FROM ubuntu:22.04
COPY start.sh /
RUN chmod +x /start.sh
RUN mkdir /etc/myprogram/
COPY myconfig.conf /etc/myprogram/
ENTRYPOINT ["bash", "/start.sh"]
