import emoji
import re
from textblob import TextBlob
import snscrape.modules.twitter as sntwitter
import pandas as pd
from googletrans import Translator
from flask import Flask, request,  render_template, url_for, redirect

# proses crawling data twitter dengan snscrape
app = Flask(__name__)
@app.route("/home")
def index(): #nama fangcion sentimen
    return render_template("index.html")

@app.route('/sentimen')
def sentimen():
        return render_template("sentimen.html")
    
@app.route('/scrolling', methods=['POST'])
def submit():
    query = request.form['query']
    pd.options.display.max_colwidth = 500
    # query = request.form['query']
    tweets = []
    limit = 100
    print("mulai crawling")
    for tweet in sntwitter.TwitterSearchScraper(query=query).get_items():
        if len(tweets) == limit:
            break
        else:
            tweets.append([tweet.content])
    df = pd.DataFrame(tweets, columns=['content'])

    def cleanTweets(text):
            text = re.sub('@[A-Za-z0-9_]+', '', text) #removes @mentions
            text = re.sub('#','',text) #removes hastag '#' symbol
            text = re.sub(r',','',text)
            text = re.sub('\[.*?\]','',text)
            text = re.sub('[()!?]','',text)
            text = re.sub('RT[\s]+','',text)
            text = re.sub('https?:\/\/\S+', '', text) 
            text = re.sub('\n',' ',text)
            text = re.sub('[0-9]+','',text)
            text = emoji.demojize(text, delimiters=("", ""))
            return text

    df['content'] = df['content'].apply(cleanTweets)

    translator = Translator()
    df['Translate'] = df['content'].apply(translator.translate, src='id',dest='en')
    df['Translate'] = df['Translate'].apply(getattr, args=('text',))

    #get subjectivity and polarity of tweets with a function
    def getSubjectivity(text):
        return TextBlob(text).sentiment.subjectivity
    #get polarity with a function
    def getPolarity(text):
        return TextBlob(text).sentiment.polarity

    df['Subjectivity'] = df['Translate'].apply(getSubjectivity)
    df['Polarity'] = df['Translate'].apply(getPolarity)

    #create a function to check negative, neutral and positive analysis
    def getAnalysis(score):
        if score<0:
            return 'Negative'
        elif score ==0:
            return 'Neutral'
        else:
            return 'Positive'
        
    df['Analysis'] = df['Polarity'].apply(getAnalysis)

    df.to_csv("hasil.csv")
    return redirect(url_for('sentimen'))
if __name__ == "__main__":
    # from waitress import serve
    # serve(app, host="0.0.0.0",port=8080)
    app.run(debug=True)
    # http_server = WSGIServer(('',5000),app)
    # http_server.serve_forever()