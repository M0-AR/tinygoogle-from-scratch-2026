FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
COPY experiments/ ./experiments/
EXPOSE 8000
CMD ["python", "-m", "src.server"]
