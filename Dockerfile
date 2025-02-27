FROM python:3.12


WORKDIR /app


COPY . /app/


RUN python3 -m venv venv


RUN . venv/bin/activate && pip install --no-cache-dir -r requirements.txt


CMD ["bash", "-c", ". venv/bin/activate && python main.py"]
