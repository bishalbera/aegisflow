FROM python:3.11-slim

WORKDIR /app

COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY mcp-server/ .

COPY data/ ./data/

RUN python data/generate_dataset.py

RUN python -c "from db import init_db; init_db()"

CMD ["python", "server.py"]
