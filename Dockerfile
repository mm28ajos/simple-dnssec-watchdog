FROM alpine:latest

# Install OS-level dependencies
RUN apk add --no-cache bind-tools python3 py3-pip py3-virtualenv curl

# Create non-root user
RUN adduser -D -u 1000 appuser

# Create virtual environment
RUN python3 -m venv /venv

# Install Python packages inside virtualenv
COPY requirements.txt /requirements.txt
RUN . /venv/bin/activate && pip install --no-cache-dir -r /requirements.txt

# Use virtualenv Python and pip by default
ENV PATH="/venv/bin:$PATH"

# Copy application code
COPY server.py /server.py

# Use non-root user
USER appuser

# Expose Flask/Gunicorn port
EXPOSE 8080

# Start with Gunicorn (production server)
CMD exec gunicorn --bind "[::]:8080" server:app
