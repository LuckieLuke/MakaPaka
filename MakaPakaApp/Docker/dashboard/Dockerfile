FROM python:3.7-alpine
WORKDIR /MakaPaka

ENV FLASK_APP dashboard.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8881

COPY ./MakaPaka /MakaPaka

RUN apk add --no-cache gcc musl-dev linux-headers openssl-dev libffi-dev
RUN pip install -r requirements.txt

CMD ["flask", "run", "--cert", "adhoc"]