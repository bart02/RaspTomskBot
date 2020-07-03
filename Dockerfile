FROM python:3.6-alpine
ADD ./requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
ADD . /app
CMD python main.py
