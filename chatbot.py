#!/usr/bin/python3
#coding=utf8
"""
q1测试集用来测试

1.先正确获取到股票名称再获取股票属性信息,或者一句话同时获取2者才能正常工作
2.可以支持一次返回多个股票的多个信息,现在支持7类 "price", "volume", "earnings", "dividends", "quote", "cap", "open"
"""

import sys
import re
from iexfinance.stocks import Stock
from iexfinance import get_available_symbols


def init_nlu():
    from rasa_nlu.training_data import load_data
    from rasa_nlu.config import RasaNLUModelConfig
    from rasa_nlu.model import Trainer
    from rasa_nlu import config

    trainer = Trainer(config.load("config_spacy.yml"))
    training_data = load_data('stock-rasa2.json')

    interpreter = trainer.train(training_data)
    return interpreter


def get_stock_names():
    l = get_available_symbols()
    names = set()
    for d in l:
        names.add(d['symbol'].lower())

    return names


def get_stock_info(names, key):
    #key in ["price", "volume", "earnings", "dividends", "quote"]
    if key == 'cap':
        key = 'market_cap'
    elif key == 'capitalization':
        key = 'market_cap'

    stock = Stock(names)
    func = getattr(stock, 'get_' + key)
    return func()


g_stock_names = get_stock_names()
# g_stock_names = set(('a', 'aa', 'amd', 'goog', "tsla", "jd", "twtr", "qcom"))
g_stock_attrs = set(("price", "volume", "earnings", "dividends", "quote", "cap", "open", "capitalization"))

STATE_INIT = INIT = 0
STATE_AUTHED = AUTHED = 1
STATE_NAME_EMPTY = 5
STATE_ATTR_EMPTY = 6
STATE_NOTHING = 7
STATE_QUIT = 100


#Which stock do you want to get a look?
state_msg = {
    STATE_INIT: "Please log in first, what's your phone number?",
    STATE_AUTHED: "Hello, what can I do for you?",
    STATE_QUIT: "It's my pleasure to help you, Bye-Bye.",

    STATE_NAME_EMPTY: "What is the stock name?",
    STATE_ATTR_EMPTY: "What kind of information do you want to know? Price? Quote? Volume? Earnings? Dividends? Open? Cap?",

    STATE_NOTHING: "Sorry, I can not follow you, Please try again",
    # STATE_WAITING_STOCK:
}

def get_resp_by_state(state, isnew=True):
    return state_msg[state]

def login(msg):

    r = re.compile(r'.*(\d{3}-?\d{4}-?\d{4}).*')  # 134-8888-8888 # 13688888888

    m = r.match(msg)
    if m and len(m.groups()) == 1:
        return 'login_ok', None, None
    else:
        return 'login_err', None, None

g_parser = init_nlu()

def nlu_parser(s):
    """
        {'intent': {'name': 'restaurant_search', 'confidence': 0.7473475191114767},
        'entities': [{'start': 14,
                    'end': 19,
                    'value': '12346',
                    'entity': 'location',
                    'confidence': 0.5345987610229831,
                    'extractor': 'ner_crf'}],
        'intent_ranking': [{'name': 'restaurant_search',
                            'confidence': 0.7473475191114767},
                            {'name': 'affirm', 'confidence': 0.08855412104912064},
                            {'name': 'greet', 'confidence': 0.06440992282016444},
                            {'name': 'goodbye', 'confidence': 0.05355980439947072},
                            {'name': 'location', 'confidence': 0.024570780280796088},
                            {'name': 'hotel_search', 'confidence': 0.021557852338971274}],
        'text': 'anywhere near 12346'}
    """
    r = g_parser.parse(s)
    # print("%s -> %s" % (s, str(r)))
    intent = r['intent']
    entities = r['entities']
    if intent['name'] == 'stock_search':
        nlu_stock_names = []
        nlu_stock_attri = []
        if entities:
            for e in entities:
                if e['entity'] == 'stock_name':
                    nlu_stock_names.append(e['value'])
                elif e['entity'] == 'stock_attri':
                    nlu_stock_attri.append(e['value'])
                else:
                    print("error1 " + str(r))

        return 'stock_search', nlu_stock_names, nlu_stock_attri
    elif intent['name'] == 'get_attri':
        # nlu_stock_names = []
        nlu_stock_attri = []
        if entities:
            for e in entities:
                if e['entity'] == 'stock_attri':
                    nlu_stock_attri.append(e['value'])
                else:
                    print("error2 " + str(r))
        return 'get_attri', None, nlu_stock_attri
    pass

state_funcs = {
    STATE_INIT: (login, "Please log in first, what's your phone number?"),
    STATE_AUTHED: (nlu_parser, "Hello, what can I do for you?"),
    STATE_QUIT: (None, "It's my pleasure to help you, Bye-Bye."),

    STATE_NAME_EMPTY: (nlu_parser, "What is the stock name?"),
    STATE_ATTR_EMPTY: (nlu_parser, "What kind of information do you want to know? Price? Quote? Volume? Earnings? Dividends? Open? Cap?"),

    STATE_NOTHING: (nlu_parser, "Sorry, I can not follow you, Please try again"),
}

def standard_keys(values, stand_keys):
    keys = []
    for v in values:
        if v in stand_keys:
            keys.append(v)
    return keys

def query(names, attrs):
    s = []
    for key in q_attri:
        v = get_stock_info(q_names, key)
        if len(q_names) == 1:
            s.append("The %s of %s is: %s" % (key, q_names[0], str(v)))
        else:
            s.append("The %s: %s" % (key, str(v)))
    print("Bot : %s" % '\n      '.join(s))

def dispatch(state, msg):
    global q_names
    global q_attri

    q = msg.upper()
    if q in {"EXIT", "BYE", "BYE-BYE", "QUIT"}:
        return STATE_QUIT, state_msg[STATE_QUIT]

    func, resp = state_funcs[state]
    t, names, attrs = func(msg)
    if names:
        names = standard_keys(names, g_stock_names)
    if attrs:
        attrs = standard_keys(attrs, g_stock_attrs)

    # print("%s-%s-%s" % (t, str(names), str(attrs)))
    if t == 'login_ok':
        return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
    elif t == 'login_err':
        return STATE_INIT, get_resp_by_state(STATE_INIT, False)
    elif t == 'stock_search' or t == "get_attri":
        if names:
            q_names = names
            # q_attri = [] #有股票名称输入了,就需要重新输入股票具体分类信息,需要看句子的上下文,也可能先说分类,第二句再问名称
        if attrs:
            q_attri = attrs

        if q_names:
            if q_attri:
                query(q_names, q_attri)
                q_names = []
                q_attri = []
                return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
            else:
                return STATE_ATTR_EMPTY, state_msg[STATE_ATTR_EMPTY]
        else:
            q_names = []
            return STATE_AUTHED, get_resp_by_state(STATE_AUTHED, False)
    elif t == 'exit':
        return STATE_QUIT, state_msg[STATE_QUIT]
    else:
        return STATE_NOTHING, state_msg[STATE_NOTHING]

    # return analyze(state, msg)


q_names = []
q_attri = []

def main():
    state = STATE_INIT
    # names = []
    print("Bot : %s" % state_msg[state])
    while True:
        q = input("User: ")
        q = q.replace("?", ' ')
        state, msg = dispatch(state, q)
        print("Bot : %s" % msg)
        if state == STATE_QUIT:
            break


def test():
    q1 = [
        '123-4567-8889',
        'I am looking for TSLA',
        'price',
        "Can you show me some infomation about TWTR",
        'cap',
        "Can you show me some infomation about jd",
        'capitalization',
        "Can you show me some infomation about qcom",
        "open and volume",
        'I want to known the volume of tsla',
        'I want to known the volume of goog',
        'I want to known the volume and the price of tsla and goog',
        'I want to known the open and the cap about goog and twtr',
        'exit',
    ]

    test_main(q1)

def test_main(ques):
    state = STATE_INIT
    print("Bot : %s" % state_msg[state])
    # m = len(ques)
    for q in ques:
        print("User: %s" % q)
        state, msg = dispatch(state, q)
        print("Bot : %s" % msg)
        if state == STATE_QUIT:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test()
    else:
        main()
