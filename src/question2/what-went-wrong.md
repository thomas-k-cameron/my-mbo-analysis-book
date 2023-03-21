# What went wrong

Here are list of reason why I decided to pass on and how I could've done differently.

I believe that I would be able to do produce some kind of result if I spend more time on it, but I decided that I have to move on because I'm not sure if I would ever be able to get something.


## Why I decided to move on

- File size is too big!

Because the feature-engineering was taking quite a lot of time, I decided create files for feature-engineered values with rust and then process that on ML algorithm written in python.

Total size of feature engineered files save in parquet format totaled to over 10 TB with strong compression (Level 15 zstd.).
I could've reduced the size but it was clear that it is going to take a lots of space.

- Cost of AWS

I was using AWS to process all the data. Cost has become a concern thanks to the size of data(storage cost) and necessary computing power.


## How I could've done differently?

- Incremental Development

I could've incrementally built my model.  
Instead of starting the model building after finishing generating data and feature-engineering the whole thing, I could've tried one by one.

I might not get what I wanted, but I think I would've at least got something.

- Reducing the size of the data

I wanted to process the data with nano seconds presicion because I wasn't able to find any one who analyzes the market in nano seconds precision. 

However, I could've grouped the data in seconds or minues to reduce the data size.

Additionally, I blindly applied many different methods when I feature-engineered each features, which is another reason that it turned into a gigantic bunch of files.
