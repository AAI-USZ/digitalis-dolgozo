FROM python:3.8.6

WORKDIR /app/ner_sentiment

COPY ./requirements.txt /app/ner_sentiment/requirements.txt
COPY ./NER-base.py /app/ner_sentiment/NER-base.py

RUN pip install -r ./requirements.txt

RUN mkdir data
RUN touch data/results_body.txt

RUN pip install transformers
RUN pip install torch