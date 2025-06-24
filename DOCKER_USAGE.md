# Docker Usage Guide for PropertySearch API

## Quick Start

### 1. Environment Setup
```bash
# Copy environment file and add your APIFY_TOKEN
cp .env.example .env
# Edit .env and add: APIFY_TOKEN=your_token_here
```

### 2. Simple Start (Recommended)
```bash
# Use the enhanced start script
./start.sh
```

### 3. Manual Docker Commands

#### Production Build
```bash
# Build and run production container
docker build -t property-agent .
docker run -d --name property-agent -p 8000:8000 --env-file .env -v $(pwd)/logs:/app/logs property-agent
```

#### Development with Auto-Reload
```bash
# Use development docker-compose for live code changes
docker-compose -f docker-compose.dev.yml up --build
```

#### Full Production Stack with Nginx
```bash
# Run with nginx reverse proxy
docker-compose --profile production up --build -d
```

## Debugging & Monitoring

### View Real-Time Logs
```bash
# View application logs
docker logs -f property-agent

# View with timestamps
docker logs -f -t property-agent

# View last 100 lines
docker logs --tail 100 property-agent
```

### Health Checks
```bash
# Quick health check
curl http://localhost:8000/health

# Detailed API test
./test_api.sh
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Log Files
- Container logs: `docker logs property-agent`
- Application logs: `./logs/property_search_YYYYMMDD.log`
- Nginx logs (if using): Docker container logs

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Property Search
```bash
POST http://localhost:8000/search
Content-Type: application/json

{
  "listing_type": "both",
  "latitude": 30.2672,
  "longitude": -97.7431,
  "radius_miles": 10.0,
  "min_rent_price": 1000,
  "max_rent_price": 3000
}
```

## Troubleshooting

### Container Won't Start
1. Check environment variables: `docker exec property-agent env`
2. Check logs: `docker logs property-agent`
3. Verify APIFY_TOKEN is set in .env file

### API Returns Errors
1. Check application logs: `docker logs property-agent`
2. Check log files: `tail -f logs/property_search_*.log`
3. Test with minimal request: `./test_api.sh`

### No Search Results
1. Verify APIFY_TOKEN is valid
2. Check Apify account quota
3. Monitor debug logs for Zillow scraper responses

### Performance Issues
1. Monitor container resources: `docker stats property-agent`
2. Check log file sizes in `./logs/`
3. Consider increasing memory limits in docker-compose.yml

## Environment Variables

- `APIFY_TOKEN`: Required - Your Apify API token
- `PORT`: Optional - API port (default: 8000)
- `PROXY_PORT`: Optional - Nginx proxy port (default: 80)
- `PROXY_SSL_PORT`: Optional - Nginx SSL port (default: 443)

## Development Tips

1. Use `docker-compose.dev.yml` for development with auto-reload
2. Mount source code volumes for live changes
3. Use DEBUG log level for detailed tracing
4. Monitor both container logs and log files simultaneously

## Production Deployment

### Render.com
The service is configured for Render deployment via `render.yaml`. Set `APIFY_TOKEN` in Render dashboard.

### Docker Swarm/Kubernetes
Use the production docker-compose.yml as a base for orchestration configurations. 