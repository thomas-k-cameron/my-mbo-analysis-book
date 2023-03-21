# Takers' Position and Execution

Based on my knowledge, financial market is a zero-sum game ran by takers and makers.
I will try to model this by consolidating the taker's position.

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

Variables suffixed with `no_vol` *un-weights* executions based on volume.

Consider a case where 2 trades are executed at 10,000 JPY, where volume is 5 and 1 each.

When the price goes up to 10,100, the profit of the synthetic position of trade is 600 JPY, but the value would be 200 JPY on `no_vol` variables.

This variants of variables gives bigger weight to small trades; There should be something to do with it.

- Taker's Synthetic Position Without Volume 

# Update Frequency 
This data is updated every time there is an execution.  
Deletion, modification or addition of order does not trigger an update.

