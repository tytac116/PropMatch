# PropMatch API Security Guide

## Overview

PropMatch API implements comprehensive security measures to protect against various attacks including DDoS, prompt injection, SQL injection, and bot abuse. This guide covers security features, configuration, and monitoring.

## Security Features

### 🛡️ Core Protection

- **Rate Limiting**: Configurable per-endpoint rate limits
- **DDoS Protection**: Automatic detection and IP blocking
- **Prompt Injection Detection**: AI input validation and sanitization
- **SQL Injection Prevention**: Pattern-based detection
- **Bot Detection**: User agent analysis and blocking
- **IP Blocking**: Automatic and manual IP management
- **Request Size Limits**: Prevent large payload attacks
- **Security Monitoring**: Real-time attack tracking and analytics

### 🔒 Rate Limiting Configuration

| Endpoint Type | Default Limit | Environment Variable |
|---------------|---------------|---------------------|
| AI Search | 10/minute | `SEARCH_RATE_LIMIT` |
| AI Explanations | 5/minute | `EXPLANATION_RATE_LIMIT` |
| General APIs | 100/minute | `GENERAL_RATE_LIMIT` |
| Admin/Sensitive | 3/minute | `STRICT_RATE_LIMIT` |

### 🚨 Attack Detection

#### Prompt Injection Patterns
- System role manipulation attempts
- Instruction bypass attempts
- Code execution attempts
- Jailbreak attempts

#### SQL Injection Patterns
- Union select statements
- Database manipulation commands
- Comment-based injections
- Stored procedure calls

#### DDoS Detection
- Request frequency analysis
- IP-based pattern recognition
- Automatic blocking thresholds

## Configuration

### Environment Variables

```bash
# Rate Limiting
SEARCH_RATE_LIMIT=10/minute
EXPLANATION_RATE_LIMIT=5/minute
GENERAL_RATE_LIMIT=100/minute
STRICT_RATE_LIMIT=3/minute

# DDoS Protection
MAX_REQUESTS_PER_IP_PER_HOUR=500
MAX_REQUESTS_PER_IP_PER_DAY=2000
SUSPICIOUS_THRESHOLD=50

# Request Limits
MAX_REQUEST_SIZE_MB=1
MAX_QUERY_LENGTH=500

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password
REDIS_RATE_LIMIT_DB=1
REDIS_SECURITY_DB=2

# Production Settings
ENVIRONMENT=production
TRUSTED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Security Features
ENABLE_RATE_LIMITING=true
ENABLE_DDOS_PROTECTION=true
ENABLE_PROMPT_INJECTION_DETECTION=true
ENABLE_IP_BLOCKING=true
ENABLE_ATTACK_MONITORING=true

# Monitoring
SECURITY_LOG_LEVEL=INFO
ENABLE_SECURITY_ALERTS=true
DEFAULT_BLOCK_DURATION_HOURS=24
MAX_BLOCK_DURATION_HOURS=168
```

### Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `TRUSTED_HOSTS` with your domain
- [ ] Set `CORS_ORIGINS` to your frontend domains only
- [ ] Use strong Redis password (`REDIS_PASSWORD`)
- [ ] Enable all security features
- [ ] Set appropriate rate limits for your traffic
- [ ] Configure proper logging and monitoring
- [ ] Use HTTPS in production
- [ ] Set up proper firewall rules
- [ ] Monitor security endpoints regularly

## Security Endpoints

### 📊 Monitoring Endpoints

All security endpoints require strict rate limiting (3 requests/minute).

#### Get Security Statistics
```http
GET /api/v1/security/stats/
```

Returns comprehensive security statistics including:
- Hourly and daily attack counts
- Top attacking IPs
- Attack type distribution
- Threat level analysis

#### Get Recent Security Events
```http
GET /api/v1/security/events/recent/?limit=50
```

Returns recent security events with details:
- Attack type and threat level
- IP address and user agent
- Endpoint targeted
- Timestamp and additional data

#### Get Blocked IPs
```http
GET /api/v1/security/blocked-ips/
```

Returns list of blocked IP addresses with:
- Block reason and duration
- Block timestamp and expiration
- Attack history

#### Generate Security Report
```http
GET /api/v1/security/report/
```

Generates comprehensive security report including:
- Attack summary and trends
- Threat distribution analysis
- Security recommendations
- Recent events and blocked IPs

### 🔧 Management Endpoints

#### Block IP Address
```http
POST /api/v1/security/block-ip/
Content-Type: application/json

{
  "ip_address": "192.168.1.100",
  "reason": "Manual block - suspicious activity",
  "duration_hours": 24
}
```

#### Unblock IP Address
```http
DELETE /api/v1/security/unblock-ip/192.168.1.100
```

#### Clear Security Events
```http
DELETE /api/v1/security/events/clear/
```

## Attack Types and Threat Levels

### Attack Types

| Type | Description | Response |
|------|-------------|----------|
| `rate_limit_exceeded` | Too many requests from single IP | Rate limiting |
| `ddos_attempt` | DDoS attack pattern detected | IP blocking |
| `prompt_injection` | Malicious AI prompt detected | Request rejection |
| `sql_injection` | SQL injection attempt | Request rejection |
| `suspicious_user_agent` | Bot/automated tool detected | Logging only |
| `large_payload` | Unusually large request | Request rejection |
| `blocked_ip_access` | Access from blocked IP | Access denied |

### Threat Levels

| Level | Description | Action |
|-------|-------------|--------|
| `low` | Minor security concern | Logged for monitoring |
| `medium` | Moderate threat | Rate limiting applied |
| `high` | Serious threat | May result in IP blocking |
| `critical` | Severe threat | Immediate IP blocking |

## Monitoring and Alerting

### Real-time Monitoring

The security system provides real-time monitoring of:
- Attack attempts and patterns
- Rate limit violations
- IP blocking events
- System health and performance

### Log Analysis

Security events are logged with structured data:
```json
{
  "timestamp": 1640995200.0,
  "ip_address": "192.168.1.100",
  "attack_type": "prompt_injection",
  "threat_level": "high",
  "endpoint": "/api/v1/search/",
  "user_agent": "curl/7.68.0",
  "blocked_content": "ignore previous instructions..."
}
```

### Automated Responses

The system automatically responds to threats:
- **Rate Limiting**: Temporary request throttling
- **IP Blocking**: Automatic blocking for severe threats
- **Request Rejection**: Immediate rejection of malicious requests
- **Alert Generation**: Real-time security alerts

## Best Practices

### 🔐 Security Hardening

1. **Use HTTPS**: Always use HTTPS in production
2. **Strong Authentication**: Implement proper API authentication
3. **Regular Updates**: Keep dependencies updated
4. **Monitoring**: Monitor security endpoints regularly
5. **Backup**: Regular backup of security configurations

### 🚀 Performance Optimization

1. **Redis Optimization**: Use Redis clustering for high traffic
2. **Rate Limit Tuning**: Adjust limits based on traffic patterns
3. **Log Management**: Implement log rotation and archival
4. **Cache Management**: Monitor Redis memory usage

### 📈 Scaling Considerations

1. **Distributed Rate Limiting**: Use Redis cluster for multiple instances
2. **Load Balancer Integration**: Configure rate limiting at load balancer
3. **Geographic Blocking**: Consider geographic IP restrictions
4. **CDN Integration**: Use CDN for additional DDoS protection

## Troubleshooting

### Common Issues

#### High False Positives
- Adjust prompt injection patterns
- Whitelist legitimate user agents
- Tune rate limiting thresholds

#### Performance Impact
- Optimize Redis configuration
- Reduce logging verbosity
- Implement caching strategies

#### Blocked Legitimate Users
- Review blocking criteria
- Implement IP whitelisting
- Adjust threat level thresholds

### Emergency Procedures

#### Under Attack
1. Monitor security dashboard
2. Identify attack patterns
3. Implement emergency rate limits
4. Block attacking IP ranges
5. Contact hosting provider if needed

#### System Recovery
1. Assess damage and impact
2. Review security logs
3. Update security configurations
4. Implement additional protections
5. Document lessons learned

## Support and Maintenance

### Regular Tasks

- [ ] Review security statistics weekly
- [ ] Update blocked IP lists
- [ ] Analyze attack patterns
- [ ] Tune rate limiting rules
- [ ] Update security configurations

### Emergency Contacts

- System Administrator: [contact info]
- Security Team: [contact info]
- Hosting Provider: [contact info]

## Compliance and Reporting

The security system maintains detailed logs for:
- Compliance auditing
- Incident response
- Performance analysis
- Security reporting

All security events are timestamped and include sufficient detail for forensic analysis and compliance reporting.

---

**Note**: This security system is designed to protect against common attacks while maintaining API performance. Regular monitoring and tuning are essential for optimal protection. 