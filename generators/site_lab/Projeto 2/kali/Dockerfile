FROM kalilinux/kali-rolling:latest@sha256:c6d78f57ebfdd9fec428a8b04f74876e66fddd08dfd328c076224a552e7332a3

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        curl \
        ffuf \
        jq \
        passwd \
        python3-setuptools \
        sqlmap \
        wfuzz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10000 lab \
    && useradd --uid 10000 --gid lab --create-home --shell /bin/bash lab \
    && install -d -o lab -g lab /workspace

COPY --chmod=0755 lab-sqli-tools.py /usr/local/bin/lab-sqli-tools
COPY --chmod=0644 encoder.py /usr/local/lib/lab-sqli/encoder.py
COPY --chmod=0755 attack-injector.py /usr/local/bin/attack-injector
RUN chmod 0755 /usr/local/lib/lab-sqli

ENV PYTHONPATH=/usr/local/lib/lab-sqli

USER lab
WORKDIR /workspace

CMD ["sleep", "infinity"]
