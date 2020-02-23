import random
import re
import string

import networkx as nx
import praw

from config.keys import (
    access_token,
    access_token_secret,
    client_id,
    client_secret,
    twitter_client_id,
    twitter_client_secret,
    user_agent,
)


def getTitle(reddit, subreddit, numberOfPosts):
    # continued from code above
    titleData = {}
    titleWords = []
    for submission in reddit.subreddit(subreddit).top(limit=numberOfPosts):
        title = submission.title
        title.translate(string.punctuation)
        titles = title.split(" ")
        titles = [x.lower().replace('"', "") for x in titles]
        titleWords.append(titles)
        for i in titles:
            if titleData.get(i, -1) == -1:
                titleData.update({i: 0})
            titleData[i] += 1
    return titleWords, titleData


def getPostText(reddit, subreddit, numberOfPosts):
    textData = {}
    textWords = []
    for submission in reddit.subreddit(subreddit).top(limit=numberOfPosts):
        text = submission.selftext
        # for i in range(len(text)):
        #   if text[i]
        text.translate(string.punctuation)
        posts = text.split(" ")
        posts = [x.lower().replace('"', "") for x in posts]
        textWords.append(posts)
        for i in posts:
            if textData.get(i, -1) == -1:
                textData.update({i: 0})
            textData[i] += 1

    return textWords, textData


def getPostSentenceList(reddit, subreddit, numberOfPosts):
    ret = []
    sentence = []
    word = ""
    for submission in reddit.subreddit(subreddit).top(limit=numberOfPosts):
        # all the titles
        contents = submission.selftext
        for i in contents:
            if i == "." or i == "!" or i == "?":
                if word:
                    sentence.append(word)
                    word = ""
                if sentence:
                    ret.append(sentence)
                    sentence = []
            elif i.strip() == "":
                if word in [
                    "a",
                    "that",
                    "can",
                    "to",
                    "in",
                    "it",
                    "was",
                    "for",
                    "on",
                    "are",
                    "as",
                    "with",
                    "at",
                    "be",
                    "this",
                ]:
                    word = word + " "
                elif word:
                    sentence.append(word)
                    word = ""
            else:
                if i != "\n":
                    word += i
    return ret


# get the frequency for words in a post
# returns a dictionary of words as keys
# and the value is the number of times
# it shows up
def getPostFreq(reddit, subreddit, numberOfPosts):
    textData = {}
    for submission in reddit.subreddit(subreddit).top(limit=numberOfPosts):
        # text is one long string
        text = submission.selftext
        text = text.lower()
        text = re.sub("[^\w]", " ", text).split()
        posts = text
        for i in posts:
            if textData.get(i, -1) == -1:
                textData.update({i: 0})
            textData[i] += 1
    return textData


class Node:
    def __init__(self, *args, **kwargs):
        self.word = kwargs.pop("word", None)
        self.frequency = kwargs.pop("frequency", None)
        self.start = kwargs.pop("start", False)
        self.start_freq = kwargs.pop("start_freq", 0)
        self.end = kwargs.pop("end", False)
        self.end_freq = kwargs.pop("end_freq", 0)

    def __str__(self):
        return self.word

    def __repr__(self):
        return self.word


def search_graph(word, g):
    for node in g.nodes:
        if node.word == word:
            return node
    return None


def build_graph(titles, freqs, g):
    for title in titles:
        ii = 0
        last_node = None
        for word in title:
            first = False
            end = False
            if word == title[0]:
                first = True
            elif word == title[-1]:
                end = True
            if not search_graph(word, g):
                freq = freqs.get(word, None)
                node = Node(word=word, frequency=freq, first=first, end=end)
                g.add_node(node)
                if first:
                    g.graph["firsts"].append(node)
                    node.start_freq += 1
                elif end:
                    g.graph["ends"].append(node)
                    node.end_freq += 1
            else:
                node = search_graph(word, g)
                if first:
                    g.graph["firsts"].append(node)
                    node.start_freq += 1
                elif end:
                    g.graph["ends"].append(node)
                    node.end_freq += 1

            if last_node:
                if g.has_edge(last_node, node):
                    g[last_node][node]["weight"] += 1
                else:
                    g.add_edge(last_node, node, weight=1)

            last_node = node

            ii += 1


def generate_title(g):
    gen_title = ""
    num_firsts = len(g.graph["firsts"])
    word = g.graph["firsts"][random.randrange(0, num_firsts)]

    while True:
        gen_title += word.word + " "
        len_edges = len(g.edges(word))
        if len_edges == 0:
            break
        l = list(g.edges(word, data=True))
        rn = []
        count = 0
        for x in l:
            new = [count] * (x[2]["weight"])
            rn += new
            count += 1
        x = random.randrange(0, len(rn))
        word = list(g.edges(word))[rn[x]][1]
        if word.end:
            if random.randrange(0, 1):
                break
    return gen_title


def get_sentences(subreddit, typ):
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    numberOfPosts = 100
    titles = []
    freqs = {}
    print("here")
    if typ == "title":
        titles, freqs = getTitle(reddit, subreddit, numberOfPosts)
    elif typ == "post":
        titles = getPostSentenceList(reddit, subreddit, numberOfPosts)
        freqs = getPostFreq(reddit, subreddit, numberOfPosts)
    g = nx.DiGraph(firsts=[], ends=[])
    build_graph(titles, freqs, g)
    ret = []
    seen = {}
    while len(ret) < 15:
        title = generate_title(g).strip()
        if not seen.get(title, None):
            ret.append(title)
            seen[title] = True
    return ret


def gen_speech(words):
    g = nx.DiGraph(firsts=[], ends=[])
    build_graph(words, {}, g)

    ret = []
    seen = {}
    while len(ret) < 10:
        gen_tweet = generate_title(g).strip()
        if not seen.get(gen_tweet, None):
            ret.append(gen_tweet)
            seen[gen_tweet] = True

    # print(ret)
    return ret


# get the top words for a frequency dictionary.
# returns a list of the top give amount of words
# in order to most to leasst frequent
def getTop(freq, amount):
    print(freq)
    # words that we do not want in the top words list
    skipWords = [
        "to",
        "a",
        "and",
        "is",
        "for",
        "be",
        "being",
        "was",
        "that",
        "have",
        "he",
        "his",
        "in",
        "the",
        "of",
        "she",
        "on",
        "had",
        "it",
        "when",
        "not",
        "at",
        "this",
        "t",
        "s",
        "i",
        "as",
        "you",
        "but",
        "so",
        "with",
        "him",
        "would",
        "should",
        "could",
        "http",
        "www",
        "https",
        "org",
        "com",
        "we",
    ]
    topVals = []
    maxVal = 0
    word = ""
    # run the amount of times asked for
    for i in range(amount):
        for key in freq:
            if freq[key] > maxVal and key not in topVals and key not in skipWords:
                maxVal = freq[key]
                word = key
        topVals.append(word)
        maxVal = 0
        word = ""
    print(topVals)
    # reutrn top values
    return topVals


subreddit = "askreddit"
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
typ = "post"
numberOfPosts = 500
freq = getPostFreq(reddit, subreddit, numberOfPosts)
# print top 10 frequent words from posts
getTop(freq, 10)

