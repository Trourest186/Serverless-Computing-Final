# Sử dụng image chứa Python
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install sudo && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt install -y python3.8

RUN apt install python3-pip -y
# Tạo thư mục làm việc
WORKDIR /app

# Sao chép mã nguồn vào thư mục làm việc
COPY main.py /app/

# Cài đặt các thư viện cần thiết (ở đây chỉ có Flask)
RUN pip install Flask

# Mở cổng 8881 để lắng nghe
EXPOSE 8888

# Chạy ứng dụng khi container được khởi chạy
CMD ["python3", "-u", "main.py"]

