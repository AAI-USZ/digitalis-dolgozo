# Import required packages
import torch
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer
import os

file_name = "./data/eslint-eslint-issues.csv"

# Create class for data preparation
class SimpleDataset:
    def __init__(self, tokenized_texts):
        self.tokenized_texts = tokenized_texts

    def __len__(self):
        return len(self.tokenized_texts["input_ids"])

    def __getitem__(self, idx):
        return {k: v[idx] for k, v in self.tokenized_texts.items()}

# Load tokenizer and model, create trainer
model_name = "siebert/sentiment-roberta-large-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
trainer = Trainer(model=model)

# Create list of texts (can be imported from .csv, .xls etc.)
pred_texts = ['I like that','That is annoying','This is great!','Wouldn´t recommend it.']

text_column = "Body"

df_pred = pd.read_csv(file_name)
pred_texts = df_pred[text_column].dropna().astype('str').tolist()


# Tokenize texts and create prediction data set
tokenized_texts = tokenizer(pred_texts,truncation=True,padding=True)
pred_dataset = SimpleDataset(tokenized_texts)

# Run predictions
predictions = trainer.predict(pred_dataset)

# Transform predictions to labels
preds = predictions.predictions.argmax(-1)
labels = pd.Series(preds).map(model.config.id2label)
scores = (np.exp(predictions[0])/np.exp(predictions[0]).sum(-1,keepdims=True)).max(1)


# Create DataFrame with texts, predictions, labels, and scores
df = pd.DataFrame(list(zip(preds,labels,scores)), columns=['pred','label','score'])
df.to_csv("SENT_results_body.csv", sep='\t')
print(df.head())
