
# Building Prediction Machine
While I failed to build anything meaningful, here are some things that I wish to pursue.

## Custom loss function for predicting the price move

Say, the Nikkei Future's market was going to move to 29,000 from 30,000. 
In directional trading, it would ok for a model to predict the market to move to 29,005, however, predicting it to become 30,995 would be a big problem.

This is the reason that wanted my model to be a classifier instead of a regressor.

I could've built a custom loss function to capture this difference, however, I thought that it would be easier to change the labels.

