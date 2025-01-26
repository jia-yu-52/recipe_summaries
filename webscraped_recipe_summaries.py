# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 20:46:50 2025

@author: jiayu
"""

from bs4 import BeautifulSoup
import requests
from fractions import Fraction
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
try:
    for dish in dishes:
        if dish.a != None:
            dish_link=dish.a['href']
            if '/recipes/food/views' in dish_link:
                html_text = requests.get(f'https://www.epicurious.com{dish_link}').text
                soup = BeautifulSoup(html_text,'lxml')
                dish_name = soup.find('h1', attrs={'data-testid': 'ContentHeaderHed'}).text
                rating = soup.find('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ RatingRating-btVmKd iUEiRd jjBDuu fOfiAf")
                if rating:
                    if float(rating.text) < min_rating:
                        continue
                    else:
                        result+=f'Dish Name: {dish_name}\nRating: {rating.text}\n'
                else:
                    result+= f'Dish Name: {dish_name}\nRating: Missing Rating\n'
                titles = soup.find_all('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ InfoSliceKey-gHIvng iUEiRd dWUQxN hykkRA")
                infos = soup.find_all('p', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ InfoSliceValue-tfmqg iUEiRd bbekcU fkSlPp")
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
                ingredients = soup.find_all('div', class_="BaseWrap-sc-gjQpdd BaseText-ewhhUZ Description-cSrMCf iUEiRd bGCtOd fsKnGI")
                for ingredient in ingredients:
                    ingredients_list.append(ingredient.text)
                string_ingredients = ', '.join(ingredients_list)
                result+=f'Ingredients: {string_ingredients}\nLink to recipe:https://www.epicurious.com{dish_link}\n\n'
finally:
    print(f'Results saved to {query} recipes.txt')
    with open(f'{query} recipes.txt', 'w', encoding='utf-8') as p:
        p.write(f'Results for {query} dishes that take up to {max_time} minutes with a minimum of {min_rating} stars:\n{result}')
