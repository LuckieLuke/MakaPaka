FROM python:3.7-alpine
WORKDIR /MakaPakaLogin

ENV FLASK_APP login.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8882
ENV FLASK_ENV development

COPY ./MakaPaka .

RUN apk add --no-cache gcc musl-dev linux-headers openssl-dev libffi-dev
RUN pip install -r requirements.txt

CMD ["flask", "run", "--cert", "adhoc"]