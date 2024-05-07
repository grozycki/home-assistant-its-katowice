FROM python:3 AS python-base
FROM homeassistant/home-assistant:latest AS home-assistant-base


FROM python-base AS python
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./your-daemon-or-script.py" ]

FROM home-assistant-base AS home-assistant
