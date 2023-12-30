# Sử dụng image Ubuntu
FROM ubuntu:latest

# Cập nhật các gói phần mềm
RUN apt-get update

# Cài đặt Nginx
RUN apt-get install -y nginx

# Mở cổng 80 cho Nginx
EXPOSE 80

# Khởi động Nginx khi container chạy
CMD ["nginx", "-g", "daemon off;"]

