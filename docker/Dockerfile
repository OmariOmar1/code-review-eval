FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==8.2.0 \
    && useradd --create-home --uid 1000 runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER runner
WORKDIR /work

CMD ["python", "-m", "pytest", "-q"]
