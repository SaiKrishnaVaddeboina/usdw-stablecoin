FROM python:3.11-slim

LABEL org.opencontainers.image.title="USDw Stablecoin Demo"
LABEL org.opencontainers.image.description="Streamlit UI for the USDw regulated stablecoin simulator"
LABEL org.opencontainers.image.source="https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install dependencies first to maximize layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY python_sim/ ./python_sim/
COPY ui/ ./ui/
COPY .streamlit/ ./.streamlit/

EXPOSE 8501

# Healthcheck — Streamlit's built-in /_stcore/health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1

CMD ["streamlit", "run", "ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
