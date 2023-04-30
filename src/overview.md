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
- [Order Book Simulator for Osaka Exchange](https://github.com/thomas-k-cameron/jpx_mbo_orderbook)
- [Data Generation with the Order Book Simulator](https://github.com/thomas-k-cameron/jpx_mbo_orderbook)
  
## Research Question  
  1. Is it true that high-speed orders are more likely to get canceled?  
    
      Yes, this is true.   
      *Slower* orders is more likely to be executed.

  3. Do market liquidity provide any information on market movement?   
      
      There are more trading opportunities when market is more liquid.  

  2. It is said that taker orders are driving force in the market; Is it true?  
      
      Statistical summary shows that distributions are different when there is a trading opportunity. (i.e. before large market move)

      
  3. Can you predict the market movement using publicly available machine learning model with the data generated above?  

       No, I couldn't make it work.  
       I tried it by using machine learning model that worked well for financial market competition on kaggle.

       I think it would've been better to model it as a stochastic process whose probability distribution evolves over time.

## Dataset  
  Dataset is the snapshot of ITCH protocol message distributed on March 2021 at Osaka Exchange.   
  ITCH is a message format widely adopted by financial exchanges and it is tailored for distributing information to market participants.  
  
  Dataset consist of over 45 billion records and size of the data exceeds 200GB.  

  For my particular dataset, it contains the information necessary to rebuild the order book for every products available;
  This includes, options, futures and combination products(calendar spread).  

## Software and Technical Infrastructure
Data is processed on AWS using `EC2 Spot Instance` and `Fargate Spot Instance` scheduled by `AWS Batch`.

  
## Kaggle Dataset  
  As part of my senior thesis, I made some of the dataset I'm using for this project partially available online.

  - [Dataset](https://www.kaggle.com/datasets/a53e93e57a1/maker-order-dataset-osaka-20210301)
  - [Notebook](https://www.kaggle.com/code/a53e93e57a1/analyzing-high-frequency-trader-by-order)
