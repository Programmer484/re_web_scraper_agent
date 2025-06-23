# 🔒 Security Guide for PropertySearch API

## Overview

This guide covers security best practices for your PropertySearch webhook API. The implementation includes multiple layers of protection.

## 🛡️ Security Layers

### 1. **API Key Authentication (Optional)**
```bash
# Set in environment
export API_KEY="your-secret-key-here"

# Use in requests
curl -X POST https://your-api.com/search \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"listing_type": "both"}'
```

### 2. **IP Whitelisting (Optional)**
```bash
# Set allowed IPs in environment
export ALLOWED_IPS="192.168.1.100,203.0.113.1,10.0.0.0/8"
```

### 3. **Rate Limiting**
- **General API**: 5 requests/second, burst 10
- **Search endpoint**: 2 requests/second, burst 5
- **Health check**: No limits

### 4. **Request Size Limits**
- Maximum request size: 1MB
- Header buffer: 4KB
- Body timeout: 12 seconds

### 5. **Input Validation**
- Pydantic models validate all input
- Geographic coordinates validation
- Enum validation for listing types
- Range validation for search parameters

## 🚨 Security Headers

All responses include:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

## 🔧 Environment Configuration

Create `.env` file with security settings:

```bash
# Required
APIFY_TOKEN=your_apify_token_here

# Security (Optional)
API_KEY=your-secret-api-key-here
ALLOWED_IPS=192.168.1.100,203.0.113.1
MAX_REQUEST_SIZE=1048576

# Application
LOG_LEVEL=DEBUG
PORT=8000
```

## 🚫 Attack Prevention

### Blocked Patterns:
- **File Extensions**: `.php`, `.asp`, `.aspx`, `.jsp`
- **SQL Injection**: Common SQL keywords in URLs
- **Sensitive Files**: `.env`, `.git`, `.htaccess`

### Method Restrictions:
- **Search endpoint**: Only POST and OPTIONS
- **Other endpoints**: GET, POST, OPTIONS only

## 📊 Security Monitoring

### Logs to Monitor:
```bash
# Security events
grep "🚫\|🔑" logs/property_search_*.log

# Failed authentication
grep "Invalid API key" logs/property_search_*.log

# Rate limit violations
grep "rate limited" /var/log/nginx/error.log

# Blocked attacks
grep "444\|403\|401" /var/log/nginx/access.log
```

### Key Metrics:
- Authentication failure rate
- IP-based request patterns
- Response time anomalies
- Error rate spikes

## 🔒 Production Security Checklist

### ✅ Essential (Before Production):
- [ ] Set strong API key (32+ characters)
- [ ] Configure IP whitelist for known clients
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up log monitoring/alerting
- [ ] Configure firewall rules
- [ ] Regular security updates

### ✅ Recommended:
- [ ] Implement request signing/HMAC verification
- [ ] Add API versioning
- [ ] Set up DDoS protection (Cloudflare/AWS Shield)
- [ ] Implement user-based rate limiting
- [ ] Add request ID tracking
- [ ] Set up automated security scanning

### ✅ Advanced:
- [ ] Web Application Firewall (WAF)
- [ ] Intrusion Detection System (IDS)
- [ ] API Gateway with additional security
- [ ] Geo-blocking for suspicious regions
- [ ] Behavioral analysis for anomaly detection

## 🚀 Quick Security Setup

### 1. **Development (Minimal Security)**
```bash
# No API key, basic logging
export API_KEY=""
./start.sh
```

### 2. **Staging (Medium Security)**
```bash
# API key + IP whitelist
export API_KEY="dev-key-12345"
export ALLOWED_IPS="your.office.ip,staging.server.ip"
./start.sh
```

### 3. **Production (Full Security)**
```bash
# Strong API key + strict IP whitelist + monitoring
export API_KEY="prod-super-secret-key-32-chars-long"
export ALLOWED_IPS="prod.client1.ip,prod.client2.ip"
docker-compose --profile production up -d
```

## 🔍 Security Testing

### Test API Key Authentication:
```bash
# Should fail without key
curl -X POST http://localhost:8000/search -d '{"listing_type":"both"}'

# Should succeed with key
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer your-api-key" \
  -d '{"listing_type":"both"}'
```

### Test Rate Limiting:
```bash
# Rapid requests should be rate limited
for i in {1..10}; do
  curl -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"listing_type":"both"}' &
done
```

### Test Input Validation:
```bash
# Should fail with validation error
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"listing_type":"invalid","radius_miles":-1}'
```

## 🆘 Incident Response

### If Compromised:
1. **Immediately**: Rotate API keys
2. **Block**: Suspicious IP addresses
3. **Monitor**: Increase logging level
4. **Analyze**: Check access logs for patterns
5. **Update**: Apply security patches
6. **Review**: Security configurations

### Emergency Contacts:
- Security team: [your-security-team@company.com]
- DevOps on-call: [your-devops-oncall@company.com]
- Hosting provider: [support ticket system]

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Nginx Security Best Practices](https://nginx.org/en/docs/http/securing_nginx.html)

---

**⚠️ Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update your security measures. 