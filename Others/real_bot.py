import pandas as pd

import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer 

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.preprocessing import LabelEncoder

from sklearn.model_selection import train_test_split

from sklearn.linear_model import LogisticRegression

from sklearn.metrics import accuracy_score, classification_report 

#load data
df = pd.read_csv('data.csv')
print(df.head())

#text Processing
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("","",string.punctuation))
    tokens = nltk.word_tokenize(text)

    cleaned = []
    for word in tokens:
        if word not in stop_words:
            cleaned.append(lemmatizer.lemmatize(word))

    return "".join(cleaned)

df['clean_text'] = df['text'].apply(preprocess_text)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['clean_text'])

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(df['label'])

print(label_encoder.classes_)

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter=1000)
model.fit(x_train,y_train)

y_pred = model.predict(x_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

def pridict_intent(text):
    clean = preprocess_text(text)
    vector = vectorizer.transform([clean])
    pridiction = model.pridict(vector)
    return label_encoder.inverse_transform(pridiction)[0]

print(pridict_intent("Sample input text to classify"))
print(pridict_intent("Another example text for prediction"))