FROM python:3.10.11-slim-bullseye

# update apt repositories, since we need git
RUN apt update

# install git, since we need it for our dependencies
RUN apt install git -y
RUN git --version

# install ffmpeg
RUN apt install ffmpeg -y
RUN ffmpeg -version

WORKDIR /app

COPY ./lib/ ./lib/
COPY ./sounds/ ./sounds/
COPY amarbot.py .
COPY requirements.txt .

# install python dependencies
RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "amarbot.py"]
