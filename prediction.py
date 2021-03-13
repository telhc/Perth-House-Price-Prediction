import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

CSV_PATH = "data/Final_Perth_Housing.csv"
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_rows", 0)

# features = ['Land_size', 'Building_size', 'Build_year', 'Sold_Price', 'Rent_Price',
#        'Bedrooms', 'Bathrooms', 'Cars', 'Last_Sold_Price', 'Postcode',
#        'CBD_distance_m', 'Closest_station_m', 'Rent_timestamp', 'Last_Sold_timestamp',
#        'Rent_Price_log', 'Rent_Price_weighted', 'Last_Sold__Price_weighted', 'Sold_Price_weighted_log',
#        'Rent_Price_weighted_log', 'Last_Sold_Price_weighted_log', 'neighbours',
#        'neighbour_avg_Sold_Price', 'neighbour_min_Sold_Price',
#        'neighbour_max_Sold_Price', 'neighbour_avg_Rent_Price',
#        'neighbour_min_Rent_Price', 'neighbour_max_Rent_Price',
#        'neighbour_avg_Last_Sold_Price', 'neighbour_min_Last_Sold_Price',
#        'neighbour_max_Last_Sold_Price', 'neighbour_avg_Sold_Price_log',
#        'neighbour_min_Sold_Price_log', 'neighbour_max_Sold_Price_log',
#        'neighbour_avg_Rent_Price_log', 'neighbour_min_Rent_Price_log',
#        'neighbour_max_Rent_Price_log', 'neighbour_avg_Sold_Price_weighted',
#        'neighbour_min_Sold_Price_weighted',
#        'neighbour_max_Sold_Price_weighted',
#        'neighbour_avg_Rent_Price_weighted',
#        'neighbour_min_Rent_Price_weighted',
#        'neighbour_max_Rent_Price_weighted',
#        'neighbour_avg_Last_Sold__Price_weighted',
#        'neighbour_min_Last_Sold__Price_weighted',
#        'neighbour_max_Last_Sold__Price_weighted',
#        'neighbour_avg_Sold_Price_weighted_log',
#        'neighbour_min_Sold_Price_weighted_log',
#        'neighbour_max_Sold_Price_weighted_log',
#        'neighbour_avg_Rent_Price_weighted_log',
#        'neighbour_min_Rent_Price_weighted_log',
#        'neighbour_max_Rent_Price_weighted_log',
#        'neighbour_avg_Last_Sold_Price_weighted_log',
#        'neighbour_min_Last_Sold_Price_weighted_log',
#        'neighbour_max_Last_Sold_Price_weighted_log',
#        'neighbour_avg_Sold_timestamp', 'neighbour_min_Sold_timestamp',
#        'neighbour_max_Sold_timestamp', 'neighbour_avg_Rent_timestamp',
#        'neighbour_min_Rent_timestamp', 'neighbour_max_Rent_timestamp',
#        'neighbour_avg_Last_Sold_timestamp',
#        'neighbour_min_Last_Sold_timestamp',
#        'neighbour_max_Last_Sold_timestamp', 'neighbour_avg_Sold_Date_diff',
#        'neighbour_min_Sold_Date_diff', 'neighbour_max_Sold_Date_diff',
#        'neighbour_avg_Land_size', 'neighbour_min_Land_size',
#        'neighbour_max_Land_size', 'neighbour_avg_Building_size',
#        'neighbour_min_Building_size', 'neighbour_max_Building_size',
#        'neighbour_avg_Bedrooms', 'neighbour_min_Bedrooms',
#        'neighbour_max_Bedrooms', 'neighbour_avg_Bathrooms',
#        'neighbour_min_Bathrooms', 'neighbour_max_Bathrooms',
#        'neighbour_avg_Cars', 'neighbour_min_Cars', 'neighbour_max_Cars']


df = pd.read_csv(CSV_PATH)

df = df.dropna(subset=["Sold_Price"])

df.Suburb.unique()
# only use housing data in metropolitan suburbs
metropolitan_suburbs = ['NEDLANDS', 'WEST PERTH', 'NORTHBRIDGE', 'EAST PERTH', 'CRAWLEY', 'PERTH']
df = df.loc[df.Suburb.apply(lambda x: x in metropolitan_suburbs)]

df = pd.concat([pd.get_dummies(df.Suburb), df], axis=1)

df = df[df.columns[df.dtypes!="object"]]

features = ["Sold_Price", "Bedrooms", "Bathrooms", "Cars", "neighbour_avg_Sold_Price", "Rent_Price", "Sold_timestamp", 
            "CRAWLEY", "EAST PERTH", "NEDLANDS", "NORTHBRIDGE",
            "PERTH", "WEST PERTH"]

df = df[features]

df.isna().sum()

df.dropna().shape

df.shape

X = df.dropna().drop("Sold_Price", axis=1)
y = df.dropna().Sold_Price

# X = df.drop("Sold_Price", axis=1)
# y = df.Sold_Price
# from sklearn.impute import SimpleImputer
# imputer = SimpleImputer(strategy="median")
# # take note of missing values
# for na_col in X.columns[X.isna().any()]:
#     X[na_col + "_was_missing"] = X[na_col].isna()

# imputed_X = pd.DataFrame(imputer.fit_transform(X))

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, test_size=0.2)


import statsmodels.api as sm

X_sm = X = sm.add_constant(X)

model = sm.OLS(y, X_sm)

model.fit().summary()

# Linear Regression
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

linear_model = LinearRegression()
linear_model_scores = -1 * cross_val_score(linear_model, X, y, cv=5, scoring='neg_mean_absolute_error')

linear_model_scores.mean()

linear_model.fit(X_train, y_train)


# Lasso Regression
from sklearn.linear_model import Lasso
lasso_model = Lasso()
lasso_model_scores = -1 * cross_val_score(lasso_model, X, y, cv=5, scoring='neg_mean_absolute_error')
lasso_model_scores.mean()

alphas = []
errors = []
for i in range(16300,16400):
    a = i/10
    alphas.append(a)
    lasso_model = Lasso(alpha=a)
    errors.append((-1*cross_val_score(lasso_model, X, y, cv=5, scoring='neg_mean_absolute_error').mean()))
    
    
plt.plot(alphas, errors)
lasso_err_df = pd.DataFrame(list(zip(alphas, errors)), columns=["alpha", "error"])
lasso_err_df[lasso_err_df.error==min(errors)]
lasso_best_alpha = lasso_err_df[lasso_err_df.error==min(errors)].alpha.to_list()[0]
lasso_model = Lasso(alpha=lasso_best_alpha)
lasso_model.fit(X_train, y_train)

# Random Forest Regressor
from sklearn.ensemble import RandomForestRegressor
rf_model = RandomForestRegressor()
rf_model_scores = -1 * cross_val_score(rf_model, X, y, cv=5, scoring='neg_mean_absolute_error')
rf_model_scores.mean()

from sklearn.model_selection import GridSearchCV
params = {"n_estimators": range(1,100,10), "criterion": ("mse", "mae"), "max_features": ("sqrt", "log2")}
gs = GridSearchCV(rf_model, params, scoring='neg_mean_absolute_error', cv=5, verbose=1)
gs.fit(X_train, y_train)
gs.best_estimator_
gs.best_score_


# XGB
from xgboost import XGBRegressor
xgb_model = XGBRegressor()
xgb_model_scores = -1 * cross_val_score(xgb_model, X, y, cv=5, scoring='neg_mean_absolute_error')
xgb_model_scores.mean()
xgbparams = {"n_estimators": range(1,100,10), "learning_rate": (0.01,0.05,0.1,0.5), "n_jobs": [4], "grow_policy": ("depthwise", "lossguide")}
xgbgs = GridSearchCV(xgb_model, xgbparams, scoring='neg_mean_absolute_error', cv=5, verbose=1)
xgbgs.fit(X_train, y_train)

from sklearn.metrics import mean_absolute_error as mae
mae(y_test, gs.best_estimator_.predict(X_test))
mae(y_test, linear_model.predict(X_test))
mae(y_test, lasso_model.predict(X_test))
mae(y_test, xgbgs.best_estimator_.predict(X_test))

plt.hist((y_test - gs.best_estimator_.predict(X_test)).abs())
(y_test - gs.best_estimator_.predict(X_test)).abs().median()
