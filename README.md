# Perth, WA House Price Prediction
* An end-to-end house price prediction project for suburbs around Perth, Western Australia.
* Scraped over 2000 entries from [housespeakingsame](http://house.speakingsame.com/) using python and selenium
* Processing of text data using regex and pandas
* Geospatial and proximity analysis with the help of [G-NAF](https://data.gov.au/data/dataset/geocoded-national-address-file-g-naf) dataset to predict house price based on neighbourhood property sales
* Optimized Linear, Lasso, and Random Forest Regressors using GridSearchCV to conclude the best model

## Data Collection / Web Scraping
Entries from house.speakingsame.com are collected with [scrape.py](https://github.com/telhc/Perth-House-Price-Prediction/blob/master/scrape.py) and saved to data/

## Combining With Geospatial Data
[gnafparse.py]() combines geospatial data obtained from data.gov.au

## Exploratory Data Analysis & Proximity Analysis
[EDA&Enrichment.ipynb]() explores correlation between property features and its respective sold price. As well as calculating average neighbourhood features by using geospatial data collected earlier.

## Prediction
[prediction.py](https://github.com/telhc/Perth-House-Price-Prediction/blob/master/prediction.py)
Use GridSearchCV and SciKit-Learn and StatsModels to optimize Linear, Lasso, XGB and Random Forest Regressors to conclude the best model with a mean absolute error of $145K.
