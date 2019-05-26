# Chatbot

This is a Chatbot project by Yutai Li to help clients with stock information.

## Snapshot

![Image text](https://github.com/whipround/Chatbot/blob/master/SnapShot.png)

## Introduction

This is a chatbot to help clients with stock information.
With this chatbot, clients can query various stock indicators conveniently.  
The chatbot model training is based on  _Rasa-nlu_.
The following techniques or methods are implemented:

- Multiple selective answers to the same question and provide a default answer.
- Intent recognition based on sklearn and spacy.
- Named entity recognition using conditional random fields.
- Construction of a local chatbot system based on _Rasa-NLU_.
- Single-round incremental query for multiple times based on the incremental filter.
- Multiple rounds of multi-query technology on state machines, and can provide explanations and answers based on contextual issues.
- Handling pending state transitions and pending actions.
- Complex pandas Dataframe processing and data cleaning, and producing a corresponding matplotlib figure.

## Example

## Identification sample

### Input: "I want to known the volume and the price of tsla and goog"

```
# Output:
{
    'intent': {
        'name': 'stock_search',
        'confidence': 0.8057684534305147},
    'entities': [
        {'start': 20, 'end': 26, 'value': 'volume', 'entity': 'stock_attri', 'confidence': 0.929808512130838, 'extractor': 'ner_crf'},
        {'start': 35, 'end': 40, 'value': 'price', 'entity': 'stock_attri', 'confidence': 0.9454178492392026, 'extractor': 'ner_crf'},
        {'start': 44, 'end': 48, 'value': 'tsla', 'entity': 'stock_name', 'confidence': 0.950630460254559, 'extractor': 'ner_crf'},
        {'start': 53, 'end': 57, 'value': 'goog', 'entity': 'stock_name', 'confidence': 0.9491938850934409, 'extractor': 'ner_crf'}],
    'intent_ranking': [
        {'name': 'stock_search', 'confidence': 0.8057684534305147},
        {'name': 'get_history_vague', 'confidence': 0.06943123805361584},
        {'name': 'get_attri', 'confidence': 0.0590244010211018},
        {'name': 'get_history', 'confidence': 0.03600855420861015},
        {'name': 'get_period', 'confidence': 0.029767353286157525}],
    'text': 'I want to known the volumeand the price of tsla and goog'
}
```

## Environment

- Python 3.4-3.7.
- Installed _iexfinance_, _spacy_.
- Installed _Rasa-nlu_. (https://www.rasa.com/docs/nlu/installation/)

## Usage

### From Terminal

Start the bot
``` bash
$python3 bot_nlu.py
```
Run the prepared test questions
``` bash
$python3 bot_nlu.py test
```

### Train the model

You can either use the given model
```
trainer = Trainer(config.load("config_spacy.yml"))
training_data = load_data('stock-rasa.json')
interpreter = trainer.train(training_data)
```
Or train a customized model by yourself
```
# Build a training file
customized_training = {
  rasa_nlu_data = {
    # Your training example here
  }
}
# Write the data into json file
with open("stock_training.json","w") as f:
    json.dump(stock_training,f)
    print('Done')
# Train the model
trainer = Trainer(config.load("config_spacy.yml"))
training_data = load_data('stock_training.json')
interpreter = trainer.train(training_data)
```
### Extract the intent and entities

```
interpreter.parse('I want to get the historical close price of tesla from Oct 12 2017 to Jan 22 2018')
```

## Contact

Email: whipround@126.com  
