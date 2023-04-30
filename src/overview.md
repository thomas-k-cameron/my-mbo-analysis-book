# Overview
- [Overview](#overview)
  - [Related Github Repositories](#related-github-repositories)
  - [Research Question](#research-question)
  - [Dataset](#dataset)
  - [Software and Technical Infrastructure](#software-and-technical-infrastructure)
  - [Kaggle Dataset](#kaggle-dataset)

This is my personal research project about analyzing the market order-by-order using snapshot of ITCH message from Osaka Exchange.

This dataset allows you to analyze every maker orders that was visible on the order book.

## Related Github Repositories
- [Order Book](https://github.com/thomas-k-cameron/jpx_mbo_orderbook)/
  
- [Code that I used for generating data with order book](https://github.com/thomas-k-cameron/jpx_mbo_features/)
  
  
## Research Question  
  1. Is it true that high-speed orders are more likely to get canceled?  
    
      Yes, this is true.   
      *Slower* orders is more likely to be executed, though there are some context to it.

  2. It is said that taker orders are driving force in the market, can they predict the market move?    
      
      I measured the taker's position in several different ways, and created a statistical summary.  
      Statistical summary shows that most variables shows different statiscial property before large market move.

  3. Do market liquidity provide any information on market movement?   
      
      Yes, it seems like it.  
      But it's complicated.
      
  4. Can you predict the market movement using publicly available machine learning model with the data generated above?  

       No, I couldn't make it work.  
       I tried it by using machine learning model that worked well for financial market competition on kaggle.

       I think it would've been better to model it as a stochastic process whose probability distribution evolves over time.

## Dataset  
  Dataset is the snapshot of ITCH protocol message distributed on March 2021 at Osaka Exchange.   
  ITCH is a message format widely adopted by financial exchanges and it is tailored for distributing information to market participants.  
  Size of the data exceeds 200GB.  

  For my particular dataset, it contains the information necessary to rebuild the order book for every products available;
  This includes, options, futures and combination products(calendar spread).  

## Software and Technical Infrastructure
- To work with 
- Order book simluator 
  Data was stored on `AWS S3` and processed with spot instances of `AWS EC2` managed by `AWS Batch`.

  
## Kaggle Dataset  
  As part of my senior thesis, I made some of the dataset I'm using for this project partially available online.

  - [Dataset](https://www.kaggle.com/datasets/a53e93e57a1/maker-order-dataset-osaka-20210301)
  - [Notebook](https://www.kaggle.com/code/a53e93e57a1/analyzing-high-frequency-trader-by-order)
