FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./

COPY src ./src
COPY schemas ./schemas
COPY storage ./storage
COPY app.py main.py ./

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "app.py"]
