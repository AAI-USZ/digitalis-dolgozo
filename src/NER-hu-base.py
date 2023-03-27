from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import csv


model = AutoModelForTokenClassification.from_pretrained("akdeniz27/bert-base-hungarian-cased-ner")
tokenizer = AutoTokenizer.from_pretrained("akdeniz27/bert-base-hungarian-cased-ner")
nlp = pipeline('ner', model=model, tokenizer=tokenizer, aggregation_strategy="first")
ner("<your text here>")


with open('./data/eslint-eslint-issues.csv', 'r', encoding='UTF-8') as issues_csv, \
     open('results_body.txt', 'w', encoding='UTF-8') as result_file:
    reader = csv.reader(issues_csv, delimiter=',')
    for row in reader:
        ner_results = nlp(row[3][2:-1])
        result_file.write(str(ner_results) + '\n')
