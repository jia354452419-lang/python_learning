FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY main.py container_status.py container_status_db.py container_status_fastapi.py dashboard.html ./

EXPOSE 8000

CMD ["python", "-m", "main"]
