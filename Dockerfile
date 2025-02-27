FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Set the entry point
ENTRYPOINT ["python", "-m", "ebay_auction_tracker.main"]

# Default command (can be overridden)
CMD ["--help"] 