FROM ollama/ollama:latest

ENTRYPOINT ["/bin/bash", "-c"]

COPY ./pull_model_and_serve.sh /usr/local/bin/pull_model_and_serve.sh
RUN chmod +x /usr/local/bin/pull_model_and_serve.sh

CMD ["/usr/local/bin/pull_model_and_serve.sh"]