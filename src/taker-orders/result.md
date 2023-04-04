# Research Question 2: Taker Orders

## Summary
Below plot is the visualization of generated data.

![plot](./summary.png)

- Reference Price  
  Reference price tracks the execution price of the future contract.

- Signal
  This is a categorical value used to group 

- Profit at Maturity Measured Against Reference Price
  This tracks taker's expected profit at maturity, it uses reference price as hypothetical final settlement price.

  Say, taker bought 5 call option at 300 whose strike price is 500.
  If the reference price is 600, then 
  - value at 0% moneyness is -200 * 5 = -1000. 
  - value at 3% moneyness is -20 * 5 = -100.
  - value at -3% moneyness is -300 * 5 = -1500.

  The plot shows the value at moneyness of 3% and -3%.

- Profit at Maturity Measured Against Reference Price un weigted 

  Same the previous data except that value is dividedd by volume.
  Say, taker bought 5 call option at 300 whose strike price is 500.
  If the reference price is 600, then 
  - value at 0% moneyness is -200. 
  - value at 3% moneyness is -20.
  - value at -3% moneyness is -300.

- Aggregated volume
  
  This is the aggregated volume within a time window.

- Number of executions
  This tracks the number of executions observed

- 

## Statistical Summary


- Unrealized Profit of Taker
Take a look at the image below.
[]

This is the aggregate unrealized profit of taker's position taken on last \\(n \\) seconds.
Unrealized profit is calculated as the absolute difference between the current mid price and the price of which it was bought/sold.

- Taker's Synthetic Position

This one is calculates the synthetic position of the all taker positions; So this is the amount of money that taker will make(lose) on maturity.

Additionally, we calculate the values for different moneyness; range is -3% ~ 3%.


I'm using the last executed price of the future contract as a reference price. For TOPIX and NK225, I'm used the large variant.

- Weighting Small Trades

I'm going to divide each trades 

Consider a case where 2 trades are executed at 10,000 JPY, where volume is 5 and 1 each.

When the price goes up to 10,100, the profit of the synthetic position of trade is 600 JPY, but the value would be 200 JPY on `no_vol` variables.

This variants of variables gives bigger weight to small trades; There should be something to do with it.

- Taker's Synthetic Position Without Volume 

# Update Frequency 
This data is updated every time there is an execution.  
Deletion, modification or addition of order does not trigger an update.

