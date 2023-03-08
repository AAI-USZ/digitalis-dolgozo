from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import csv

tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

nlp = pipeline("ner", model=model, tokenizer=tokenizer)

with open('./data/eslint-eslint-issues.csv', 'r', encoding='UTF-8') as issues_csv, \
     open('results_body.txt', 'w', encoding='UTF-8') as result_file:
    reader = csv.reader(issues_csv, delimiter=',')
    for row in reader:
        ner_results = nlp(row[3][2:-1])
        result_file.write(str(ner_results) + '\n')
