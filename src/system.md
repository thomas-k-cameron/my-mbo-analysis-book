# Overview of System/Tools/Software
- [Overview of System/Tools/Software](#overview-of-systemtoolssoftware)
  - [Order Book Simulator](#order-book-simulator)
  - [Cloud Environment](#cloud-environment)
  - [Future Direction](#future-direction)
    - [Order Book](#order-book)
    - [Automate things](#automate-things)

## Order Book Simulator

Order book simluator is built from scratch with Rust based on specification provided by Japan Exchange Group.  
It works with Osaka Exchange's ITCH procotol message.

Current implementation requires all data to be loaded onto the RAM.
The original dataset was not sorted by timestamp and I didn't want to mess around with the data as I was concerned that I might break it without noticing it.

List of things that I can improve is mentioned on future direction.

## Cloud Environment
I used AWS, but I believe same can be done in other platform as well.

Here are my reasoning for using S3 over other services.

- Data Storage: Object Storage vs MySQL/PostgresDB vs Serverless databases     
  - Object Storage  
    Least expensive and as long as you keep the file size small, it work.   
    Schema is not required, so it's not difficult to introduce new data types.

  - Server RDBMS (e.g. MySQL, PostgresDB)   
    Server is quite expensive and query wasn't always as fast.  
    Since most my dataset was read only so most features were not necessary.  

  - Serverless DB  
    You will only be charged for what you use but you could mess up your query and end up with 1000 USD an hour. (it happened to me.)
    Since most my dataset was read only so most features were not necessary.  

I almost exclusively used EC2 but this is what I found out about AWS's computing services.

- Computing: EC2 vs Lambda vs Fargate  
  - EC2
    - Predictable Hardware
      You know exactly what hardware you are getting. This is important especially when you want to use language like Rust, which compile down to native binary.

    - Wide range of configuration to choose from
    - Good discount with spot instances
  - Fargate
    - Un-predictable hardware  
      You don't know what CPU you are getting  
    - Less configuration is required for Fargate  
      AWS batch is quite tricky with EC2 but this is not the case with Fargate.

    - Slightly more expensive compared to EC2
  - Lambda
    - Works very well if you can divide up your jobs into smaller pieces
    - Job must be completed in 15 Minutes
    - No spot instance
    - Hardware configuration is not flexible 
    - You can use it with S3 batch operation

## Future Direction
### Order Book
Things that I would do to improve:

- Multi-threading
- Loading Data By Streaming
- Generics To Work With Different Message Format (e.g. FIX format, JSON format from crypto exchanges)

Performance optimization will allow you to,
- work with smaller instance
- allows you to work with smaller quotas
- work in faster iteration 

### Automate things
- Reducing the file size to allow use of solutions such as S3 Batch operations to further drive the cost down.
- Indexing of generated data
- CI/DC
- Benchmarking... etc