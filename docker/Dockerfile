FROM amazonlinux
# Comment
WORKDIR /root/
RUN yum -y install python3
RUN yum -y install python3-pip
RUN yum -y update
RUN pip3 install pandas polars tensorflow
RUN pip3 install boto3
RUN pip3 install zstd
RUN pip3 install pyarrow
ADD . .
CMD python3 /root/main.py