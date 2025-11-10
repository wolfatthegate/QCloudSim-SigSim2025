FROM python:3.10-slim-buster
WORKDIR .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["bash", "-lc", "python Section-6-Use-case-1.py && python Section-6-Use-case-2.py"]