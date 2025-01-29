# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 20:46:50 2025

@author: jiayu
"""

from bs4 import BeautifulSoup
import requests
from fractions import Fraction
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error
from selenium import webdriver

def info_extraction(link):
    driver = webdriver.Chrome()
    driver.get(link)
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    dish_name = soup.find('h1', attrs={'data-testid': 'ContentHeaderHed'}).text
    reviews_extract = soup.find_all('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ ReviewText-jEXzdO iUEiRd bjMGUM fMdFQx")
    rating = soup.find('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ RatingRating-btVmKd iUEiRd jjBDuu fOfiAf")
    titles = soup.find_all('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ InfoSliceKey-gHIvng iUEiRd dWUQxN hykkRA")
    infos = soup.find_all('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ InfoSliceValue-tfmqg iUEiRd bbekcU fkSlPp")
    ingredients = soup.find_all('div', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ Description-cSrMCf iUEiRd bGCtOd fsKnGI")
    driver.quit()
    return dish_name, reviews_extract, rating, titles, infos, ingredients

def estimator(file_name): 
    reviews_data = pd.read_csv(file_name)
    reviews = reviews_data['Review']
    criteria = reviews_data[['Ease of cooking', 'Taste', 'Versatility', 'Generic']]
    reviews_train, reviews_test, criteria_train, criteria_test = train_test_split(reviews, criteria, random_state=1)
    tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
    reviews_train_tfidf = tfidf.fit_transform(reviews_train)
    reviews_test_tfidf = tfidf.transform(reviews_test)
    sample_reviews = tfidf.transform(reviews)
    avg_mse = {}
    for i in [10,50,100,200,300,400,500]:
        rf_regressor = RandomForestRegressor(n_estimators=i, random_state=1)
        multioutput_regressor = MultiOutputRegressor(rf_regressor)
        multioutput_regressor.fit(reviews_train_tfidf, criteria_train)
        criteria_pred = multioutput_regressor.predict(reviews_test_tfidf)
        mses = []
        for j, label in enumerate(criteria.columns):
            mse = mean_squared_error(criteria_test[label], criteria_pred[:, j])
            mses.append(mse)
        avg_mse[i] = sum(mses)/len(mses)
    estimator = min(avg_mse, key=avg_mse.get)
    final_rf_regressor = RandomForestRegressor(n_estimators=estimator, random_state=1)
    final_model = MultiOutputRegressor(final_rf_regressor)
    final_model.fit(sample_reviews, criteria)
    return tfidf, final_model  

def criteria_score(reviews_from_recipe, tfidf, final_model):
    reviews_tfidf = tfidf.transform(reviews_from_recipe)
    criteria_pred = final_model.predict(reviews_tfidf)
    criteria_pred = pd.DataFrame(criteria_pred, columns=['Ease of cooking', 'Taste', 'Versatility', 'Generic'])
    average_scores = criteria_pred.mean()
    return average_scores

print("What is the main ingredient or theme you would like to have today?")
query = input('Main ingredient/theme: ')
query_key=query.replace(' ', '+')
print("What is the maximum amount of time you would like to spend on cooking today?")
max_time = int(input('Maximum time in minutes: '))
print("What is the minimum rating that you would like the recipe to have? ")
min_rating = float(input('Rating: '))
print(f'Searching for {query} dishes that take up to {max_time} minutes with a minimum of {min_rating} stars...')
main_search_text = requests.get(f'https://www.epicurious.com/search?q={query_key}').text
main_soup = BeautifulSoup(main_search_text, 'lxml')
dishes = main_soup.find_all('div', class_="ClampContent-hilPkr fvKowN")
result = ''
tfidf, final_model = estimator("training_recipe.csv")
try:
    for dish in dishes:
        if dish.a != None:
            dish_link=dish.a['href']
            if '/recipes/food/views' in dish_link:
                dish_name, reviews_extract, rating, titles, infos, ingredients = info_extraction(f'https://www.epicurious.com{dish_link}')
                if rating:
                    if float(rating.text) < min_rating:
                        continue
                    else:
                        result+=f'Dish Name: {dish_name}\nRating: {rating.text}\n'
                else:
                    result+= f'Dish Name: {dish_name}\nRating: Missing Rating\n'
                for title, info in zip(titles, infos):
                    time_required = 0
                    serving = 0
                    if title.text == "Total Time":
                        try:
                            time_string = info.text.strip()
                            if 'hours' in time_string:
                                hours,time_string = time_string.split('hours')
                                time_required += float(Fraction(hours))*60
                            if 'hour' in time_string:
                                hours,time_string =time_string.split('hour')
                                time_required += float(Fraction(hours))*60
                            if 'minutes' in time_string:
                                minutes,_ = time_string.split('minutes')
                                time_required+= float(Fraction(minutes))
                            time_required = int(time_required)
                            if time_required > max_time:
                                continue
                            result+=f'Time Required: {(time_required)} minutes\n'
                        except ValueError:
                               time_required = info.text.strip()       
                               result+=f'Time Required: {(time_required)}\n'
                    if title.text == "Yield":
                        serving = info.text
                        result+=f'Serving Size: {serving}\n'
                ingredients_list=[]
                for ingredient in ingredients:
                    ingredients_list.append(ingredient.text)
                string_ingredients = ', '.join(ingredients_list)
                result+=f'Ingredients: {string_ingredients}\n'
                if reviews_extract:
                    reviews_from_recipe = []
                    for review in reviews_extract:
                        reviews_from_recipe.append(review.text)
                    reviews_from_recipe = pd.DataFrame(reviews_from_recipe, columns=['Review'])
                    average_scores = criteria_score(reviews_from_recipe['Review'], tfidf, final_model)
                    result+='\n'.join([f"{col}: {score:.5f}" for col, score in average_scores.items()])
                result+=f'\nLink to recipe: https://www.epicurious.com{dish_link}\n\n'                
                
finally:
    print(f'Results saved to {query} recipes.txt')
    with open(f'{query} recipes.txt', 'w', encoding='utf-8') as p:
        p.write(f'Results for {query} dishes that take up to {max_time} minutes with a minimum of {min_rating} stars:\n{result}')
