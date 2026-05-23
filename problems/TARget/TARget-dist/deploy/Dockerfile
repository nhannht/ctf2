FROM python:3.14-slim

COPY flag /flag
RUN mv /flag /flag-`cat /proc/sys/kernel/random/uuid`.txt

WORKDIR /app

COPY src/app.py /app/app.py

RUN pip install flask

EXPOSE 5000

CMD ["python3", "app.py"]