from flask import Flask,request,render_template,redirect
import sqlite3 as sql
import pandas as pd
import numpy as np
import pickle
import bs4 as bs
import re

from nltk.corpus import stopwords


def review_cleaner(review):
    '''
    Clean and preprocess a review.
    
    1. Remove HTML tags
    2. Use regex to remove all special characters (only keep letters)
    3. Make strings to lower case and tokenize / word split reviews
    4. Remove English stopwords
    5. Rejoin to one string
    '''
    
    #1. Remove HTML tags
    review = bs.BeautifulSoup(review).text
    
    #2. Use regex to find emoticons
    emoticons = re.findall('(?::|;|=)(?:-)?(?:\)|\(|D|P)', review)
    
    #3. Remove punctuation
    review = re.sub("[^a-zA-Z]", " ",review)
    
    #4. Tokenize into words (all lower case)
    review = review.lower().split()
    
    #5. Remove stopwords
    eng_stopwords = set(stopwords.words("english"))
    review = [w for w in review if not w in eng_stopwords]
    
    #6. Join the review to one sentence
    review = ' '.join(review+emoticons)
    # add emoticons to the end

    return(review)


app = Flask(__name__)
placeholder = [None]

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/data")
def list():
    con = sql.connect("database2.db")
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select * from sentiment")

    rows = cur.fetchall()
    return render_template("data.html",rows = rows)

@app.route("/",methods = ['POST'])
@app.route("/home",methods = ['POST'])
def submit_review():
    if request.method == "POST":
        text = request.form["text1"]

        cleaner = review_cleaner
        vect = pickle.load(open('vectorize.pkl','rb'))
        model = pickle.load(open('model.pkl','rb'))

        clean_text = cleaner(text)
        v = vect.transform([clean_text])
        prediction = model.predict(v)[0]
        if prediction == 1:
            sent = "Positive"
        else:
            sent = "Negative"
        
        prob = model.predict_proba(v).max()

        conn = sql.connect('database2.db')
        maxid = conn.execute("select max(id) from sentiment").fetchall()[0][0]

        if not maxid:
            maxid = 0
        maxid+=1
        conn.execute("INSERT INTO sentiment VALUES (?,?,?,?)",(maxid,text,sent,"-"))
        conn.commit()
        conn.close()

        placeholder[-1]=[sent,prob,text]

        return redirect("/result")
        
        
@app.route("/result")
def res():
    return render_template(
        "result.html",
        value1 = placeholder[-1][0],
        value2 = placeholder[-1][1],
        value3 = placeholder[-1][2])

@app.route("/result", methods = ['POST'])
def feedback():
    if request.method == "POST":
        feed = request.form["rate"]
        
        con = sql.connect('database2.db')
        maxid = con.execute("select max(id) from sentiment").fetchall()[0][0]

        if maxid:
            con.execute(f"""update sentiment 
                        set feedback = "{feed}"
                        where id = "{maxid}"  
                        """)
        
        con.commit()
        con.close()
        
        return render_template("thanks.html")

if __name__ == "__main__":
    app.run()