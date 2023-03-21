# Software Engineering/Cloud Computing

## Automated benchmarking, capasity optimization, code organization
OutOfMemory error and timeout was one of the most common error that I ran into.  
I was able to fix it by simple up-scaling my instance, but it was annoying, took some time, and not cost efficient.

This can be optimized by benchmarking it against few samples datasets, estimating how much time/ram it would take.

I think the best way to implement this is by github workflow(or something similar).
I can tag a git commit which I want to run my test/benchmark against; trigger github workflow, then automatically create a report, post it on github.

This can help me organize my code better as well; I ran into situation where some of my code went missing.
I tried to investigate by reading through git commits took a lot of time, as pretty much everything was in a single repository.

## Data format for storing data
Most of my data I generated is stored in CSV format compressed with zstd.  

I wanted to stay away from formats like parquet because I didn't want it to write schema file when using rust.

I realized later that I could simply use `polars` library on rust ot infer schema; Parquet is lot more efficient compared to CSV. 

I will stop using CSV files all together and stick with parquet.

## Optimizing Order Book Simulator
- RAM
Current implementation of order book requires to load up the data on the RAM before it can start processing.

The ITCH dataset is unsorted, so you don't really know where the message you need to process exists until you read it to the end.
I could've created a sorted copy, however, I was concerened that I might make a mistake when I create the new dataset and not realize that until very later.

However, this resulted in high memory requirement.

- CPU

