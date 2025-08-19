# Deployment Guide

This guide covers various deployment options for the Value Investing Stock Finder application.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Considerations](#production-considerations)
5. [Monitoring and Logging](#monitoring-and-logging)

## Local Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/stock-finder.git
   cd stock-finder
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application:**
   ```bash
   python src/main.py
   ```

### Development Commands

```bash
# Run tests
make test

# Run linting
make lint

# Format code
make format

# Run security checks
make security

# Generate coverage report
make coverage
```

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose

### Quick Start

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Run in background:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f stock-finder
   ```

### Manual Docker Build

1. **Build the image:**
   ```bash
   docker build -t value-investing-stock-finder .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name stock-finder \
     -e FINNHUB_API_KEY=your_key \
     -e SEC_API_KEY=your_key \
     -v $(pwd)/reports:/app/reports \
     -v $(pwd)/logs:/app/logs \
     value-investing-stock-finder
   ```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name stock-finder
   ```

2. **Build and push image:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   docker tag value-investing-stock-finder:latest your-account.dkr.ecr.us-east-1.amazonaws.com/stock-finder:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/stock-finder:latest
   ```

3. **Create ECS task definition and service**

#### Using AWS Lambda

1. **Package for Lambda:**
   ```bash
   pip install -r requirements.txt -t lambda-package/
   cp -r src/* lambda-package/
   cd lambda-package && zip -r ../lambda-deployment.zip .
   ```

2. **Deploy to Lambda with appropriate timeout and memory settings**

### Google Cloud Platform

#### Using Cloud Run

1. **Build and deploy:**
   ```bash
   gcloud builds submit --tag gcr.io/your-project/stock-finder
   gcloud run deploy stock-finder \
     --image gcr.io/your-project/stock-finder \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Azure

#### Using Azure Container Instances

1. **Build and push to Azure Container Registry:**
   ```bash
   az acr build --registry your-registry --image stock-finder .
   ```

2. **Deploy to Container Instances:**
   ```bash
   az container create \
     --resource-group your-rg \
     --name stock-finder \
     --image your-registry.azurecr.io/stock-finder:latest \
     --environment-variables FINNHUB_API_KEY=your_key SEC_API_KEY=your_key
   ```

## Production Considerations

### Environment Variables

Set these environment variables in production:

```bash
# Required
FINNHUB_API_KEY=your_finnhub_api_key
SEC_API_KEY=your_sec_api_key

# Optional (with defaults)
MIN_MARKET_CAP=100000000
MAX_PE_RATIO=30
MIN_ROE=30
MIN_GROSS_MARGIN=40
MIN_SALES_GROWTH=15
CACHE_DURATION=3600
MAX_CONCURRENT_REQUESTS=5
```

### Security

1. **API Key Management:**
   - Use environment variables or secret management services
   - Rotate keys regularly
   - Monitor API usage

2. **Network Security:**
   - Use HTTPS for all external communications
   - Implement rate limiting
   - Use VPC for cloud deployments

3. **Data Protection:**
   - Encrypt sensitive data at rest
   - Implement proper access controls
   - Regular security audits

### Performance Optimization

1. **Caching:**
   - Implement Redis for distributed caching
   - Use CDN for static assets
   - Cache API responses appropriately

2. **Database:**
   - Use connection pooling
   - Implement proper indexing
   - Regular maintenance

3. **Monitoring:**
   - Set up application performance monitoring
   - Monitor API rate limits
   - Track error rates

## Monitoring and Logging

### Logging Configuration

The application uses Python's built-in logging module. Configure logging levels:

```python
import logging

# Production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

The application includes health check endpoints:

```bash
# Check application health
curl http://localhost:8000/health

# Check API connectivity
curl http://localhost:8000/health/api
```

### Metrics Collection

Consider implementing metrics collection:

1. **Application Metrics:**
   - Request/response times
   - Error rates
   - API call success rates

2. **Business Metrics:**
   - Number of companies analyzed
   - Analysis completion time
   - Report generation success

3. **Infrastructure Metrics:**
   - CPU and memory usage
   - Disk I/O
   - Network traffic

### Alerting

Set up alerts for:

- High error rates
- API rate limit warnings
- Disk space usage
- Memory usage
- Application downtime

## Troubleshooting

### Common Issues

1. **API Rate Limits:**
   - Implement exponential backoff
   - Use multiple API keys
   - Cache responses

2. **Memory Issues:**
   - Process data in batches
   - Implement garbage collection
   - Monitor memory usage

3. **Network Issues:**
   - Implement retry logic
   - Use connection pooling
   - Monitor network latency

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export DEBUG=1
python src/main.py
```

### Log Analysis

Use log analysis tools:

```bash
# View recent errors
grep ERROR logs/app.log | tail -20

# Monitor API calls
grep "API call" logs/app.log | tail -10

# Check performance
grep "Analysis completed" logs/app.log | tail -5
```

## Support

For issues and questions:

1. Check the [README.md](README.md) for basic usage
2. Review the [test files](tests/) for examples
3. Open an issue on GitHub
4. Contact the development team

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
