from transformers import OpenAIGPTTokenizer, OpenAIGPTModel
# import torch
import spacy
import requests
import stock_price_loader as spl

tokenizer = OpenAIGPTTokenizer.from_pretrained('openai-gpt')
model = OpenAIGPTModel.from_pretrained('openai-gpt', return_dict=True)

fw = spl.FinWorld()

bs = fw.msft.news

for dct in bs:
    print(dct['link'])
    txt = requests.get(dct['link']).text
    inputs = tokenizer(txt, return_tensors="pt")
    outputs = model(**inputs)

    last_hidden_states = outputs.last_hidden_state
    print(last_hidden_states.shape)
    print(last_hidden_states)
