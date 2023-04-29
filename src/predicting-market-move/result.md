# Research Question 4: Predicting Market Move
## Overview
I tried to predict the market move using machine leanring model that was available online.

I couldn't simply download a jupyter notebook and make it work, so I had to make changes here and there, but it's essentially the same as the ML model that took the 1st place on [Jane Street Market Prediction](https://www.kaggle.com/competitions/jane-street-market-prediction/discussion/224348).

I trained them using the dataset I used to for other research questions. Labels are the Buy/Sell/Timeout groups that I discussed earlier.

## Result
It simply didn't work; Timeout is the only value that trained model ever produce.


## Why it didn't work
- Difference in Dataset  
  My dataset has different distribution/values compared to what the model was developed for.  
  Variance is lot smaller and data point is lot larger.
- Scale of the dataset
  Number variables and data points that my dataset have is significantly larger than the dataset used in kaggle competition. 
 
  While I don't think this was the root cause, I think it might have affected in one way or another.

## Things that I tried but didn't work
- File size is too big!
I tried to improve the algorithm by increasing the number of variables with feature-engineering.

Because the feature-engineering was taking quite a lot of time, I decided create files for feature-engineered values with rust and then process that on ML algorithm written in python.

Total size of feature engineered files saved in parquet format totaled to over 10 TB with strong compression (Level 15 zstd.).
I could've reduced the size but it was clear that it is going to take a lots of space.

This also turned the cost of AWS as a primary concern.


## How I could've done differently

- Incremental Development

I could've incrementally built my model.  
Instead of starting the model building after finishing generating data and feature-engineering the whole thing, I could've tried one by one.

I might not get what I wanted, but I think I would've at least got something.

- Reducing the size of the data

I wanted to process the data with nano seconds presicion because I wasn't able to find any one who analyzes the market in nano seconds precision. 

However, I could've grouped the data in seconds or minues to reduce the data size.

Additionally, I blindly applied many different methods when I feature-engineered each features, which is another reason that it turned into a gigantic bunch of files.
