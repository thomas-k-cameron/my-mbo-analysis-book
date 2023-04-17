# Overview of System/Tools/Software

## Current Implementation

- Order Book Simulator
Order book simluator is built from scratch with Rust.  
It works with Osaka Exchange's ITCH procotol message.

- Cloud Environment
I used AWS, but I believe same can be done in other platform as well.

Data is stored on S3 bucket. It appeared to be lot cheaper, faster, and easier to iterate than DBMS. 

Processing of data makes heavy use of spot instances (EC2 and Fargate) and it is scheduled by AWS Batch.

- mdbook
This website is built with mdbook.


## Future Direction
### Order Book
Current implementation requires all data to be loaded onto the RAM.
The original dataset was not sorted by timestamp and I didn't want to mess around with the data as I was concerned that I might break it without noticing it.

Things that I would do to improve:

- Multi-threading
- Loading Data By Streaming
- Generics To Work With Different Message Format (e.g. FIX format, JSON format from crypto exchanges)

Performance optimization will allow you to,
- work with smaller instance
- allows you to work with smaller quotas
- work in faster iteration 

### Things to automate
- Indexing of generated data
- CI/DC
- Benchmarking... etc