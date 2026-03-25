# Stage 1: Build React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
ENV REACT_APP_BACKEND_URL=""
ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max-old-space-size=2048
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --network-timeout 120000
COPY frontend/ .
RUN yarn build

# Stage 2: Python backend + serve static frontend
FROM python:3.11-slim
WORKDIR /app

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
    fastapi==0.110.1 \
    uvicorn==0.25.0 \
    motor==3.3.1 \
    pydantic==2.12.5 \
    openpyxl==3.1.5 \
    "qrcode[pil]==8.2" \
    httpx==0.28.1 \
    "python-jose[cryptography]==3.5.0" \
    "passlib[bcrypt]==1.7.4" \
    python-dotenv==1.2.1 \
    python-multipart==0.0.22 \
    bcrypt==4.1.3 \
    Pillow

RUN pip install --no-cache-dir \
    --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ \
    emergentintegrations

COPY backend/ .
COPY --from=frontend-build /build/build ./static

EXPOSE 8001
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"
