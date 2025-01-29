**Summary**: Recipes on Epicurious were filtered according to:
1. The dish to be cooked or the main ingredient/theme to be worked with
2. Maximum time to be spent on cooking
3. Minimum rating the recipe should have
Afterwards, webscraping was utilised to extract the following:
1. Dish name
2. Rating
3. Cooking time required
4. Serving size
5. Ingredients list
6. Reviews (used to generate scores for attributes of the recipe -- 'Ease of Cooking', 'Taste', 'Versatility', 'Generic', with the help of a Random Forest model which uses 50 reviews from various Epicurious recipes as training data) 
These information are then written into a text file for users' perusal.
