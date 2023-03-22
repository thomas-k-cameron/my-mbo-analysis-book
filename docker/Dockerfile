FROM amazonlinux
# Comment
WORKDIR /root/
COPY ./main.py .
RUN yum -y install python3
RUN yum -y install python3-pip
RUN yum -y update
RUN pip3 install pandas polars tensorflow
RUN pip3 install boto3
CMD python3 /root/main.py