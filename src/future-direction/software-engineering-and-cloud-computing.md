# Software Engineering/Cloud Computing

## Automated benchmarking, capasity optimization, code organization
OutOfMemory error and timeout was one of the most common error that I ran into.  
I was able to fix it by upscaling it, however, this is expensive and it took me some time.

I think I can take a benchmark against small dataset, before moving on to running it on the large data.

I think the best way to implement this is by github workflow(or something similar).
I can tag a git commit which I want to run my test/benchmark against; trigger github workflow, then automatically create a report, post it on github.

This can help me organize my code better as well; I ran into situation where some of my code went missing.
I tried to investigate by reading through git commits took a lot of time, as pretty much everything was in a single repository.

## Data format for storing data
Most of my data I generated is stored in CSV format compressed with zstd.  

After some experiments, I found out that parquet format is lot more efficient because,
- It is a binary format
- I don't need to decompress the whole data before reading it

I tried `feather` as well, however, the format doesn't support compression, and I found out that parquet was more efficient in terms of storage space.

I think I would not use CSV format if I were to do it again.

## Optimizing Order Book Simulator
The current implementation of the order book simluator is very inefficient, but I had some good reason for this.

- RAM
Current implementation of order book requires to load up the data on the RAM before it can start processing.

The ITCH dataset is unsorted, so you don't really know where the message you need to process exists until you read it to the end.
I could've created a sorted copy, however, I was concerened that I might make a mistake when I create the new dataset and not realize that until very later.

However, this resulted in high memory requirement.

- CPU
While I did implement multi-threading to some extent when I was generating one of the data I was trying to use it for machine learning, the order book is basically single-threaded.

It was lot simpler to implement it without multi-threading, however, I think this is the priority. 