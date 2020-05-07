import re
import nltk
import math
import nltk.corpus
import operator
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords
from nltk.stem import wordnet
from nltk import ne_chunk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
from collections import Counter
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer



class textAnalytics(object):

    def __init__(self,file1):
        self.limit = 10
        self.stringsList = []
        self.file1 = file1
        self.review_df = pd.read_csv(self.file1)
        self.token_pattern = '(?u)\\b\\w+\\b'
        self.field = 'text'
        #print(list(self.review_df))
        self.review_df = self.review_df[['text','cool','useful','funny','review_count','stars']]
        self.stopWords = stopwords.words('english')
        #print(self.stopWords)
        
    def bowConverter(self):
        bow_converter = CountVectorizer(token_pattern=self.token_pattern)
        x = bow_converter.fit_transform(self.review_df[self.field])
        self.words = bow_converter.get_feature_names()
        #print(len(words)) ## 29221
        
    def biGramConverter(self):
        bigram_converter = CountVectorizer(ngram_range=(2,2), token_pattern=self.token_pattern)
        x2 = bigram_converter.fit_transform(self.review_df[self.field])
        self.bigrams = bigram_converter.get_feature_names()
        #print(len(bigrams)) ## 368937
        #print(bigrams[-10:])
        ##        ['zuzu was', 'zuzus room', 'zweigel wine'
        ##       , 'zwiebel kräuter', 'zy world', 'zzed in'
        ##       , 'éclairs napoleons', 'école lenôtre', 'ém all', 'òc châm']

    def triGramConverter(self):
        trigram_converter = CountVectorizer(ngram_range=(3,3), token_pattern=self.token_pattern)
        x3 = trigram_converter.fit_transform(self.review_df[self.field])
        self.trigrams = trigram_converter.get_feature_names()
        print(len(self.trigrams)) # 881609
        #print(self.trigrams[:10])
        ##        ['0 0 eye', '0 20 less', '0 39 oz', '0 39 pizza', '0 5 i'
        ##         , '0 50 to', '0 6 can', '0 75 oysters', '0 75 that', '0 75 to']

    def gramPlotter(self):
        self.bowConverter()
        self.biGramConverter()
        self.triGramConverter()
        
        sns.set_style("darkgrid")
        counts = [len(self.words), len(self.bigrams), len(self.trigrams)]
        plt.plot(counts, color='cornflowerblue')
        plt.plot(counts, 'bo')
        plt.margins(0.1)
        plt.xticks(range(3), ['unigram', 'bigram', 'trigram'])
        plt.tick_params(labelsize=14)
        plt.title('Number of ngrams in the first 10,000 reviews of the Yelp dataset', {'fontsize':16})
        plt.show()

    def wordLem(self):
        self.bowConverter()
        for line in self.words:
            print(line+":"+lemmatizer.lemmatize(line))

    def wordCount(self):
        for line in self.review_df[self.field]:
            wordsTokens = word_tokenize(line)
            self.stringsList.append(Counter(wordsTokens))
        ##  Counter({'.': 11, 'the': 9, 'and': 8, 'was': 8, 'It': 5, 'I': 5, 'it': 4, 'their': 4

    def stringCleaning(self):
        self.wordCount()
        lengthList = []
        punctuationList = ['-?','!',',',':',';','()',"''",'.',"``",'|','^','..','...']
        for i in range(0,self.limit):
            for words in self.stringsList[i]:
                if len(words)>0:
                    lengthList.append(words)
        post_punctuation = [word for word in lengthList if word not in punctuationList]
        noStopWords = [word for word in post_punctuation if word not in self.stopWords]
        self.postPunctCount = Counter(noStopWords)
        ## print(self.postPunctCount)
        ##        Counter({'I': 9, "n't": 6, 'The': 5, 'go': 5, 'good': 5, "'s": 5,
        ##                 'My': 4, 'It': 4, 'place': 4, 'menu': 4, ')': 4, 'outside': 3,
        ##                 'food': 3, 'like': 3, "'ve": 3, 'amazing': 3, 'delicious': 3,
        ##                 'came': 3, 'wait': 3, 'back': 3, 'They': 3, 'evening': 3, 'try': 3,
        ##                 'one': 3, '(': 3, 'awesome': 3,'much': 3, 'took': 2, 'made': 2,
        ##                 'sitting': 2, 'Our': 2, 'arrived': 2, 'quickly': 2, 'looked': 2, ....

    def tagsMaker(self):
        # If you want to run this code, install Ghostscript first
        self.stringCleaning()
        tags = nltk.pos_tag(self.postPunctCount)
        grams = ne_chunk(tags)
        grammers = r"NP: {<DT>?<JJ>*<NN>}"
        chunk_parser = nltk.RegexpParser(grammers)
        chunk_result = chunk_parser.parse(grams)
        print(chunk_result)
        ##        (ORGANIZATION General/NNP Manager/NNP Scott/NNP Petello/NNP)
        ##          (NP egg/NN)
        ##          Not/RB
        ##          (NP detail/JJ assure/NN)
        ##          albeit/IN
        ##          (NP rare/JJ speak/JJ treat/NN)
        ##          (NP guy/NN)
        ##          (NP respect/NN)
        ##          (NP state/NN)
        ##          'd/MD
        ##          surprised/VBN
        ##          walk/VB
        ##          totally/RB
        ##          satisfied/JJ
        ##          Like/IN
        ##          always/RB
        ##          say/VBP
        ##          (PERSON Mistakes/NNP)


url = ('https://raw.githubusercontent.com/thomasawolff/verification_text_data/master/YelpReviews10000.csv')

go = textAnalytics(url)
#go.bowConverter()
##go.gramPlotter()
#go.wordLem()
##go.wordCount()
##go.stringCleaning()
go.tagsMaker()
##go.computeIDF()
