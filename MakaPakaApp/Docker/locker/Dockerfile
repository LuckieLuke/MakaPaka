FROM python:3.7-alpine
WORKDIR /MakaPakaLockers

ENV FLASK_APP lockers.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8887
ENV FLASK_ENV development

COPY ./MakaPakaLockers .

RUN apk add --no-cache gcc musl-dev linux-headers openssl-dev libffi-dev
RUN pip install -r requirements.txt

CMD ["flask", "run", "--cert", "adhoc"]