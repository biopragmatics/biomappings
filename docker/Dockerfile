FROM python:3.9

RUN git clone --branch dockerize https://github.com/biopragmatics/biomappings.git && \
    cd biomappings && \
    pip install -e .[web]

ENTRYPOINT ["biomappings", "web"]
