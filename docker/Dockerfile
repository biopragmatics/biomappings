FROM python:3.9

# Note: you can only clone HTTP anonymously so we clone using HTTPs
# and then use sed to rewrite the remote to be SSH-based
RUN git clone https://github.com/biopragmatics/biomappings.git && \
    cd biomappings && \
    sed -i 's/https:\/\/github.com\//git@github.com:/g' .git/config && \
    pip install -e .[web]

COPY startup.sh /startup.sh
ENTRYPOINT ["/startup.sh"]
