# Stage 1: Build React frontend
FROM node:18-slim AS frontend-build
WORKDIR /build
COPY frontend/ .
RUN yarn install --network-timeout 120000
ENV REACT_APP_BACKEND_URL=""
ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max-old-space-size=2048
RUN yarn build

# Stage 2: Python backend + serve static frontend
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

COPY backend/ .
COPY --from=frontend-build /build/build ./static

EXPOSE 8001
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"
