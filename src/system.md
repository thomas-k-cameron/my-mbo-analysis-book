# Overview of System/Tools/Software
- [Overview of System/Tools/Software](#overview-of-systemtoolssoftware)
  - [Current Implementation](#current-implementation)
    - [Order Book Simulator](#order-book-simulator)
    - [Cloud Environment](#cloud-environment)
  - [Future Direction](#future-direction)
    - [Order Book](#order-book)
    - [Things to automate](#things-to-automate)



## Current Implementation

### Order Book Simulator

Order book simluator is built from scratch with Rust.  
It works with Osaka Exchange's ITCH procotol message.

### Cloud Environment
I used AWS, but I believe same can be done in other platform as well.

- Data Storage   
    All data is stored on S3.     
    Compared to DB systems like DynamoDB or MySQL, it is lot cheaper.  
    You cannot execute complex queries but I didn't need it.

- Computing  
    Data is processed with EC2/Fargate scheduled with Batch.  
    I used Spot instances exclusively to optimize the cost.

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
- Reducing the file size to allow use of solutions such as S3 Batch operations to further drive the cost down.
- Indexing of generated data
- CI/DC
- Benchmarking... etc