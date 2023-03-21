# Overview 
This is my personal research project about Limit Order Book Reconstruction with snapshot of ITCH messages, and building a prediction machine based on that. 

- Research Question  
  1. Is it true that high-speed orders are more likely to get canceled?
  2. Can you build a prediction machine?

  2nd research question didn't work out well.   
  I detailed out what I tried, and why I decided to move on without any proper result.

- Dataset  
  Dataset is the snapshot of ITCH protocol message distributed on March 2021 at Osaka Exchange.
  ITCH is a message format widely adopted by financial exchanges and it is tailored for distributing information to market participants.  
  Size of the data exceeds 200GB.  

  For my particular dataset, it contains the information necessary to re-build the order book for every products available;
  This includes, Options, Futures and Combination products.  

- Technical Infrastructure  
  Data was stored on `S3` and processing happened on `EC2` managed by `Batch`.

- LOB Simluation Software   
  Software for LOB reconstruction is developed from scratch, solely by me. It is written in Rust, based on the specification provided by JPX.   
  Callback based interface allows you to capture updates that happens on the order book.

- Machine Learning, Data Analysis
  I used python when I wanted to take advantage of the eco-system.
  For tasks that python isn't fast enough, I used Rust.

- Kaggle Dataset  
  As part of my senior thesis, I made some of the dataset I'm using for this project partially available online.

  https://www.kaggle.com/datasets/a53e93e57a1/maker-order-dataset-osaka-20210301
