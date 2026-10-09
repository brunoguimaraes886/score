# Imagem oficial e publica do Mockserver (ARQ-05, ARQ-07).
FROM mockserver/mockserver:5.15.0

# ARQ-12: as respostas do Banco Central (CDI diario, serie 12 do SGS), uma
# por dia de calendario, geradas por scripts/download_cdi.py. O Mockserver
# carrega o arquivo quando sobe.
COPY cdi_expectations.json /config/cdi_expectations.json
ENV MOCKSERVER_INITIALIZATION_JSON_PATH=/config/cdi_expectations.json
