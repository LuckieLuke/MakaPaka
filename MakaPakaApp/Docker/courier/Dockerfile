FROM python:3.7-alpine
WORKDIR /MakaPakaCourier

ENV FLASK_APP courier.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8885
ENV FLASK_ENV development

COPY ./MakaPakaCourier .

RUN apk add --no-cache gcc musl-dev linux-headers openssl-dev libffi-dev
RUN pip install -r requirements.txt

CMD ["flask", "run", "--cert", "adhoc"]