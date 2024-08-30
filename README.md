# nulp-chatbot

**Create Virtual environment.**

- python -m venv ~/envs/chatbotnew/

**Activate virtual environment.**

- source ~/envs/chatbotnew/bin/activate

**Install requirements**

- pip install -r requirements.txt (update requirements.txt with actual
  file name).

Note: If some libraries not installed from the requirements file then install them manualy

**Run Chatbot**

- python3 app.py

## Docker

1. Build

- ` docker build -t chatbotapp .`

2. Create network if required

- `docker network create my_network`
- `docker network connect my_network pg-db`

3. Run the Container

- `docker run  --name chatbotapp --network my_network --env-file .env -p 5000:5000 chatbotapp`
