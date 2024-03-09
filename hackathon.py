# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1D1pr08irn96z5udKMQ1hTPvAZjRmDnz0
"""

!pip install optuna swifter

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import optuna
from sklearn.model_selection import learning_curve
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, recall_score, classification_report
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import swifter
import re
from sklearn.model_selection import cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import uniform
import random
import string
from wordcloud import WordCloud

from google.colab import drive
drive.mount('/content/drive')

book = pd.read_csv('/content/drive/MyDrive/Books.csv')
ratings = pd.read_csv('/content/drive/MyDrive/Ratings.csv')
users = pd.read_csv('/content/drive/MyDrive/Users.csv')

book.isnull().sum()

book.nunique()

"""#EDA"""

merged_df = pd.merge(book, ratings, on='ISBN')

final_df = pd.merge(merged_df, users, on='User-ID')
final_df.head()

final_df.info()

final_df.shape

final_df.isnull().sum()

final_df.drop(columns=['Image-URL-L','Publisher'],inplace = True)
final_df['Age'].fillna(final_df['Age'].median(),inplace = True)
final_df['Book-Author'].fillna(final_df['Book-Author'].mode()[0],inplace = True)

final_df.isnull().sum()

sample_size = 1000
sample_df = final_df.sample(n=sample_size, random_state=42)
sample_df['Rating_Category'] = pd.cut(sample_df['Book-Rating'], bins=[0, 3, 7, 10], labels=['Low', 'Medium', 'High'])
plt.figure(figsize=(16, 150))
sns.barplot(data=sample_df, x='Book-Rating', y='Book-Author', hue='Rating_Category', palette={'Low': 'red', 'Medium': 'yellow', 'High': 'green'})
plt.title('Average Rating by Author')
plt.xlabel('Average Rating')
plt.ylabel('Book Author')
plt.legend(title='Rating Category')
plt.show()

"""#average rating by book title

"""

sample_size = 1000
sample_df = final_df.sample(n=sample_size, random_state=42)
sample_df['Rating_Category'] = pd.cut(sample_df['Book-Rating'], bins=[0, 3, 7, 10], labels=['Low', 'Medium', 'High'])
plt.figure(figsize=(16, 150))
sns.barplot(data=sample_df, x='Book-Rating', y='Book-Title', hue='Rating_Category', palette={'Low': 'red', 'Medium': 'yellow', 'High': 'green'})
plt.title('Average Rating by Title of Book')
plt.xlabel('Average Rating')
plt.ylabel('Title of Book')
plt.legend(title='Rating Category')
plt.show()

final_df.isna().sum()

final_df['Age'] = final_df['Age'].astype(int)
final_df['Book-Rating'] = final_df['Book-Rating'].astype(int)
final_df['User-ID '] = final_df['User-ID'].astype(int)

final_df.duplicated().sum()

final_df = final_df[final_df['Book-Rating']!=0]

final_df[final_df['Book-Rating'] == 0].value_counts().head(10)

sample_size = 1000
sample_df = final_df.sample(n=sample_size, random_state=42)
sample_df['Rating_Category'] = pd.cut(sample_df['Book-Rating'], bins=[0, 3, 7, 10], labels=['Low', 'Medium', 'High'])
plt.figure(figsize=(16, 150))
sns.barplot(data=sample_df, x='Book-Rating', y='Book-Title', hue='Rating_Category', palette={'Low': 'red', 'Medium': 'yellow', 'High': 'green'})
plt.title('Average Rating by Title of Book')
plt.xlabel('Average Rating')
plt.ylabel('Title of Book')
plt.legend(title='Rating Category')
plt.show()

age_q1 = final_df['Age'].quantile(0.25)
age_q3 = final_df['Age'].quantile(0.75)
age_iqr = age_q3 - age_q1
age_lower_bound = age_q1 - 1.5 * age_iqr
age_upper_bound = age_q3 + 1.5 * age_iqr
final_df = final_df[(final_df['Age'] >= age_lower_bound) & (final_df['Age'] <= age_upper_bound)]
year_q1 = final_df['Year-Of-Publication'].astype(int).quantile(0.25)
year_q3 = final_df['Year-Of-Publication'].astype(int).quantile(0.75)
year_iqr = year_q3 - year_q1
year_lower_bound = year_q1 - 1.5 * year_iqr
year_upper_bound = year_q3 + 1.5 * year_iqr
final_df = final_df[(final_df['Year-Of-Publication'].astype(int) >= year_lower_bound) & (final_df['Year-Of-Publication'].astype(int) <= year_upper_bound)] # Removes rows that have 'Year-Of-Publication' values ​​outside the range [year_lower_bound, year_upper_bound]
final_df.describe()

pd.set_option('display.max_colwidth', None)

title_sample = final_df[['ISBN', 'Book-Title']].sample(20) # let's see sample title of book

print(title_sample.to_string(index=False))

Genres = ['Fiction', 'Novel', 'Adventure', 'Romance', 'History', 'Thriller', 'Horror', 'Biography', 'Fantasy' ,'Other']

sentences = [title.split() for title in final_df['Book-Title']]

model = Word2Vec(sentences, vector_size=500, window=5, min_count=5, sg=2)

def clean_text(text):
    # Removes special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    return text

# Define function to predict genre from book title
def predict_genre(book_title):
    clean_title = clean_text(book_title)
    title_words = clean_title.split()

    # Check if title_words is empty
    if not title_words:
        return 'Other'

    # Filter title words that are present in the Word2Vec model vocabulary
    title_words = [word for word in title_words if word in model.wv]

    # Check if there are words left after filtering
    if not title_words:
        return 'Other'

    # Get the average word vector for the title
    title_vector = sum([model.wv[word] for word in title_words]) / len(title_words)

    # Find the most similar genre based on cosine similarity
    most_similar_genre = None # Initial genre
    max_similarity = -1
    for genre in Genres:
        genre_vector = model.wv[genre]
        similarity = cosine_similarity([title_vector], [genre_vector])[0][0] # cosine_similarity : search for similarities between two vectors in multidimensional
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_genre = genre

    return most_similar_genre

book_title_to_predict = "Wie man einen Mann aufreisst (Heyne BÃ¼cher)"
predicted_genre = predict_genre(book_title_to_predict) # Genre predict of the book

print(f"The predicted genre for '{book_title_to_predict}' is {predicted_genre}.")

final_df['Genre'] = final_df.apply(lambda row: predict_genre(row['Book-Title']), axis=1)

final_df

final_df.to_csv('/content/drive/MyDrive/final_df_modified.csv', index=False)

final1_df = pd.read_csv('/content/drive/MyDrive/final_df_modified.csv')

final1_df.head()

genre_counts = final_df['Genre'].value_counts
genre_counts()

genre_counts = genre_counts()  # Call the function to get the data

plt.figure(figsize=(10, 6))
genre_counts.plot(kind='bar', color='skyblue')
plt.title('Number of Books in Each Genre')
plt.xlabel('Genre')
plt.ylabel('Total Books')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

X = final_df['Book-Title']
y = final_df['Genre']

# Splitting the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42, stratify=y)

# TF-IDF vectorization
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Initialize and train Naive Bayes classifier
nb_classifier = MultinomialNB()
nb_classifier.fit(X_train_tfidf, y_train)

# Predictions
y_pred = nb_classifier.predict(X_test_tfidf)

# Calculate accuracy
print("Accuracy train:", accuracy_score(y_train, nb_classifier.predict(X_train_tfidf)))
print("Accuracy test:", accuracy_score(y_test, y_pred))

param_grid = {
    'alpha': uniform(0.01, 10)  # Uniform distribution for alpha
}

# Initialize the Naive Bayes classifier
nb_classifier = MultinomialNB()

# Perform Random Search
random_search = RandomizedSearchCV(nb_classifier, param_distributions=param_grid, n_iter=50, cv=5, scoring='accuracy', random_state=42)
random_search.fit(X_train_tfidf, y_train)

# Get the best hyperparameters
best_alpha = random_search.best_params_['alpha']

# Initialize and train Naive Bayes classifier with the best hyperparameters
best = MultinomialNB(alpha=best_alpha)
best.fit(X_train_tfidf, y_train)

# Predictions
y_pred = best.predict(X_test_tfidf)

print("\nNaive Bayes (after tuning with Random Search):")
print("Best Alpha:", best_alpha)
print("Accuracy train:", accuracy_score(y_train, best.predict(X_train_tfidf)))
print("Accuracy test:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

corpus = (final_df['Book-Title'] + ' ' + final_df['Genre']).apply(str.split).tolist()

word2vec_model_recommender = Word2Vec(sentences=corpus, vector_size=500, window=5, min_count=5, sg=2)

def get_recommendations(title, genre, data, word2vec_model):
    # Combine title and genre into one text
    text = title + ' ' + genre

    # Tokenize text
    tokens = text.split()

    # Get average vector for tokens
    vectors = [word2vec_model.wv[token] for token in tokens if token in word2vec_model.wv]
    if len(vectors) == 0:
        return None

    avg_vector = sum(vectors) / len(vectors)

    # Calculate cosine similarity with all other books
    similarities = []
    recommended_titles = set()  # Set to store titles of recommended books
    for idx, row in data.iterrows():
        other_vectors = [word2vec_model.wv[token] for token in row['Book-Title'].split() if token in word2vec_model.wv]
        if len(other_vectors) > 0:
            other_avg_vector = sum(other_vectors) / len(other_vectors)
            similarity = cosine_similarity([avg_vector], [other_avg_vector])[0][0]
            similarities.append((row, similarity))

    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Get top 10 unique recommendations
    recommendations = []
    for book, sim in similarities:
        if book['Book-Title'] not in recommended_titles and book['Book-Rating'] > 5:
            recommendations.append(book.to_dict())
            recommended_titles.add(book['Book-Title'])
        if len(recommendations) >= 10:
            break

    df_recommendations = pd.DataFrame(recommendations)

    return df_recommendations

recommendations = get_recommendations("Harry potter ", "Fantasy", final_df.sample(10000), word2vec_model_recommender)
recommendations

