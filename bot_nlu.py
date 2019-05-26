#!/usr/bin/python3
#coding=utf-8
"""
用法:
1.用代码中的q1测试集来测试
python3.7 bot_nlu.py q1
2.用户终端输入问题来测试
python3.7 bot_nlu.py

其他:
1.此实现必须要按照顺序来,先正确获取到股票名称再获取股票属性信息,或者一句话同时获取2者才能正常工作
2.可以支持一次返回多个股票的多个信息,具体要支持哪些信息,需要明确需求,现在只支持7类 "price", "volume", "earnings", "dividends", "quote", "cap", "open"
"""
import sys
import re
import random
from datetime import datetime
from iexfinance.stocks import Stock
from iexfinance import get_available_symbols
from iexfinance.stocks import get_historical_data

def init_nlu():
    from rasa_nlu.training_data import load_data
    from rasa_nlu.config import RasaNLUModelConfig
    from rasa_nlu.model import Trainer
    from rasa_nlu import config

    trainer = Trainer(config.load("config_spacy.yml"))
    # training_data = load_data('stock-rasa2.json')
    training_data = load_data('stock-rasa.json')

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


# 调试的时候用下面的一行,速度会快一些,不用每次都初始化
# g_stock_names = get_stock_names()
g_stock_names = set(('a', 'aa', 'amd', 'goog', "tsla", "jd", "twtr", "qcom", "aapl"))

g_stock_attrs = set(("price", "volume", "earnings", "dividends", "quote", "cap", "open", "capitalization", 'close'))

STATE_INIT = INIT = 0
STATE_AUTHED = AUTHED = 1
STATE_NAME_EMPTY = 5
STATE_ATTR_EMPTY = 6
STATE_NOTHING = 7
STATE_PERIOD_EMPTY = 8
STATE_QUIT = 100


#Which stock do you want to get a look?
state_msg = {
    STATE_INIT: "Please log in first, what's your phone number?",
    STATE_AUTHED: ("Hello, what can I do for you?", "I'm waiting for you", "What do you want to know", ),
    STATE_QUIT: ("It's my pleasure to help you, Bye-Bye.", "Bye", "See you next time"),

    STATE_NAME_EMPTY: ("What is the stock name?", "Sorry, I still don't know the stock name"),
    STATE_ATTR_EMPTY: ("What kind of information do you want to know? Price? Quote? Volume? Earnings? Dividends? Open? Cap?",
                        "Price? Quote? Volume? Earnings? Dividends? Open? Cap?",
                        ),
    STATE_PERIOD_EMPTY: "Tell me the date range please.",
    STATE_NOTHING: ("Sorry, I can not follow you, Please try again",
                    "Sorry, I'm still learning, try another question",
                    ),
    # STATE_WAITING_STOCK:
}

def get_resp_by_state(state, isnew=True):
    q = state_msg[state]
    if type(q) == str:
        return q
    else:
        r = random.randint(0, len(q)-1)
        return q[r]

def login(msg):
    #根据输入决定是否允许login,或者提示用户要login

    r = re.compile(r'.*(\d{3}-?\d{4}-?\d{4}).*')  # 134-8888-8888 # 13688888888

    m = r.match(msg)
    if m and len(m.groups()) == 1:
        return 'login_ok', None, None, None
    else:
        return 'login_err', None, None, None

g_parser = init_nlu()

def get_entities(intent, entities):
    nlu_stock_names = []
    nlu_stock_attri = []
    nlu_stock_period = [None, None]
    if entities:
        for e in entities:
            if e['entity'] == 'stock_name':
                nlu_stock_names.append(e['value'])
            elif e['entity'] == 'stock_attri':
                nlu_stock_attri.append(e['value'])
            elif e['entity'] == 'start_date':
                nlu_stock_period[0] = (e['value'])
            elif e['entity'] == 'end_date':
                nlu_stock_period[1] = (e['value'])
            else:
                print("error1 " + str(r))

    return intent, nlu_stock_names, nlu_stock_attri, nlu_stock_period

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
    return get_entities(intent['name'], entities)

state_funcs = {
    STATE_INIT: (login, "Please log in first, what's your phone number?"),
    STATE_AUTHED: (nlu_parser, "Hello, what can I do for you?"),
    STATE_QUIT: (None, "It's my pleasure to help you, Bye-Bye."),

    STATE_NAME_EMPTY: (nlu_parser, "What is the stock name?"),
    STATE_ATTR_EMPTY: (nlu_parser, "What kind of information do you want to know? Price? Quote? Volume? Earnings? Dividends? Open? Cap?"),
    STATE_PERIOD_EMPTY: (nlu_parser, ""),

    STATE_NOTHING: (nlu_parser, "Sorry, I can not follow you, Please try again"),
}

def standard_keys(values, stand_keys):
    keys = []
    for v in values:
        sv = v.lower()
        if sv in stand_keys:
            keys.append(sv)
    return keys

def query(names, attrs):
    s = []
    for key in q_attri:
        v = get_stock_info(q_names, key)
        if len(q_names) == 1:
            s.append("The %5s of %5s is: %s" % (key, q_names[0], str(v)))
        else:
            s.append("The %6s: %s" % (key, str(v)))
    print("Bot : %s" % '\n      '.join(s))

def get_day_by_str(s):
    return datetime.strptime(s, "%Y - %m - %d").date()


def fmt_day_attris(df, names, day, attris):
    def f(v):
        if attris:
            for a in attris:
                # print('v', v)
                if a == 'volume':
                    l.append('%10s |' % v[a])
                else:
                    l.append('%7s |' % v[a])
        else:
            l.append('%7s |%7s |%7s |%7s |%10s |' % (v['open'], v['close'], v['low'], v['high'], v['volume']))

    l = ['| ', day, ' |']
    if len(names) == 1:
        v = df[day]
        f(v)
    else:
        for name in names:
            v = df[name][day]
            f(v)

    return ''.join(l)


def get_column(names, attirs):
    if not attirs:
        return len(names) * 48 + 14
    c = 14

    x = 9 * len(attirs)
    if 'volume' in attirs:
        x += 3

    return c + len(names) * x
    # return c

def fmt_names_attris(names, attris):
    l = []
    column = get_column(names, attris)
    name_col = (column - 14) // len(names)

    s = '|            |'
    for name in names:
        # s += '%25s                        |' % name
        i = len(name)
        sep = name_col - i
        if sep % 2 == 0:
            s += ' ' * (sep//2) + name + ' ' * (sep//2 - 1 ) + '|'
        else:
            s += ' ' * (sep//2) + name + ' ' * (sep//2) + '|'

    l.append('-' * column)
    l.append(s)
    l.append('-' * column)

    s1 = '|    date    |'
    for name in names:
        if attris:
            for a in attris:
                if a == 'volume':
                    s1 += '%9s  |' % a
                else:
                    s1 += '%6s  |' % a
        else:
            s1 += '%6s  |%6s  |%6s  |%6s  |%9s  |' % ('open', 'close', 'low', 'high', 'volume')

    l.append(s1)
    l.append('-' * column)
    return '\n'.join(l)

def fmt_df(df, names, wanted, days=None):
    def f(s):
        return datetime.strptime(s, "%Y-%m-%d").date()

    if len(names) > 1:
        names = list(df.keys())
        days = list(df[names[0]].keys())
    else:
        days = list(df.keys())

    days = [f(day) for day in days]
    days = sorted(days)

    print(fmt_names_attris(names, wanted))

    for day in days:
        s = day.strftime("%Y-%m-%d")
        print(fmt_day_attris(df, names, s, wanted))

    print('-' * get_column(names, wanted))


def query_his(names, attrs, period):
    start, end = period
    start = get_day_by_str(start)
    end = get_day_by_str(end)

    # print('query_his', names, attrs, start, end)
    df = get_historical_data(names, start, end)

    # print('df', df)
    print("Bot : ")
    fmt_df(df, names, attrs)

    # print("Bot : %s" % str(df))

def dispatch(state, msg):
    global q_names
    global q_attri

    q = msg.upper()
    if q in {"EXIT", "BYE", "BYE-BYE", "QUIT"}:
        return STATE_QUIT, get_resp_by_state(STATE_QUIT)

    func, _ = state_funcs[state]
    t, names, attrs, period = func(msg)
    # print('nlu_parser', t, names, attrs, period)

    if names:
        names = standard_keys(names, g_stock_names)
    if attrs:
        attrs = standard_keys(attrs, g_stock_attrs)

    # print('nlu_parser->2', t, names, attrs, period)

    if t == 'login_ok':
        return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
    elif t == 'login_err':
        return STATE_INIT, get_resp_by_state(STATE_INIT, False)
    elif t == 'stock_search' or t == "get_attri":
        # print('qnames', q_names, names, attrs)
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
                return STATE_ATTR_EMPTY, get_resp_by_state(STATE_ATTR_EMPTY)
        else:
            q_names = []
            return STATE_AUTHED, get_resp_by_state(STATE_AUTHED, False)
    elif t == 'get_history':
        query_his(names, attrs, period)
        return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
    elif t == 'get_period':
        if attrs:
            pass
        else:
            attrs = q_attri

        query_his(q_names, attrs, period)
        return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
        # if q_names:
        #     query_his(q_names, q_attri, period)
        #     return STATE_AUTHED, get_resp_by_state(STATE_AUTHED)
        # else:
        #     return STATE_NOTHING, state_msg[STATE_NOTHING]
    elif t == 'get_history_vague':
        if names:
            q_names = names
        if attrs:
            q_attri = attrs
        return STATE_PERIOD_EMPTY, get_resp_by_state(STATE_PERIOD_EMPTY)
    elif t == 'exit':
        return STATE_QUIT, get_resp_by_state(STATE_QUIT)
    else:
        return STATE_NOTHING, get_resp_by_state(STATE_NOTHING)

    # return analyze(state, msg)


q_names = []
q_attri = []

def main():
    global g_stock_names
    g_stock_names = get_stock_names()
    print("load %d stock names" % len(g_stock_names))

    state = STATE_INIT
    # names = []
    print("Bot : %s" % get_resp_by_state(state))
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
        # 'I am looking for TSLA',
        # 'price',
        # "Can you show me some infomation about TWTR",
        # 'cap',
        "Can you show me some infomation about qcom",
        "open and volume",
        # 'I want to known the volume of goog',
        'I want to known the volume and the price of tsla and goog',
        'i want to get the historical open price of apple from 2019-4-1 to 2019-4-10',
        "give me the historical data of TSLA and GOOG",
        "from 2019-5-1 to 2019-5-5",
        "show me the data of TSLA in the past few days",
        "open and close data from 2018-1-1 to 2018-1-5",
        'exit',
    ]

    test_main(q1)

def test_main(ques):
    state = STATE_INIT
    print("Bot : %s" % get_resp_by_state(state))
    # m = len(ques)
    for q in ques:
        print("User: %s" % q)
        state, msg = dispatch(state, q)
        print("Bot : %s" % msg)
        if state == STATE_QUIT:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("load %d stock names" % len(g_stock_names))
        test()
    else:
        main()
