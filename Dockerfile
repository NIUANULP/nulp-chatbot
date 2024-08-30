FROM python:3.8-slim

# Install gcc and other necessary build tools
RUN apt-get update && apt-get install -y gcc g++ make

WORKDIR /app

COPY requirements3.txt .

# Install dependencies from all requirements files
RUN pip install --no-cache-dir -r requirements3.txt

COPY . .

CMD ["python3", "app.py"]
