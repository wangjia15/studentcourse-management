# Chinese University Grade Management System - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Chinese University Grade Management System in production environments.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Database Setup](#database-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **Memory**: 8 GB RAM
- **Storage**: 100 GB SSD
- **Network**: 1 Gbps connection
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### Recommended Requirements
- **CPU**: 8 cores
- **Memory**: 16 GB RAM
- **Storage**: 200 GB SSD
- **Network**: 10 Gbps connection
- **Load Balancer**: Nginx / HAProxy
- **CDN**: CloudFlare / AWS CloudFront

### Software Dependencies
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+
- Python 3.11+

## Environment Configuration

### 1. Environment Variables

Create a `.env` file with the following configuration:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grade_management
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Application Configuration
SECRET_KEY=your_very_long_and_secure_secret_key_here
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
SMTP_HOST=smtp.university.edu.cn
SMTP_PORT=587
SMTP_USER=system@university.edu.cn
SMTP_PASSWORD=your_email_password
SMTP_TLS=true

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_PATH=/app/uploads
ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,jpeg,png

# Security Configuration
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true

# Monitoring Configuration
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### 2. SSL/TLS Configuration

Generate SSL certificates:

```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Or use self-signed certificates for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/private.key \
  -out nginx/ssl/certificate.crt
```

## Docker Deployment

### 1. Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/chinese-university-grade-management.git
cd chinese-university-grade-management

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Start the application
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Production Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Initialize database
docker-compose exec app python init_db.py

# Create admin user
docker-compose exec app python -m app.scripts.create_admin
```

### 3. Scaling Services

```bash
# Scale application instances
docker-compose up -d --scale app=3

# Scale worker processes
docker-compose up -d --scale worker=2
```

## Manual Deployment

### 1. Backend Deployment

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
  postgresql-15 redis-server nginx certbot

# Create application user
sudo useradd -m -s /bin/bash gradeapp
sudo su - gradeapp

# Clone repository
git clone https://github.com/your-org/chinese-university-grade-management.git
cd chinese-university-grade-management/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env

# Initialize database
python init_db.py

# Create systemd service
sudo tee /etc/systemd/system/gradeapp.service > /dev/null <<EOF
[Unit]
Description=Grade Management System
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=gradeapp
Group=gradeapp
WorkingDirectory=/home/gradeapp/chinese-university-grade-management/backend
Environment=PATH=/home/gradeapp/chinese-university-grade-management/backend/venv/bin
ExecStart=/home/gradeapp/chinese-university-grade-management/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable gradeapp
sudo systemctl start gradeapp
```

### 2. Frontend Deployment

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build frontend
cd ../frontend
npm install
npm run build

# Configure Nginx
sudo tee /etc/nginx/sites-available/grade-management > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    client_max_body_size 10M;

    location / {
        root /home/gradeapp/chinese-university-grade-management/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/grade-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Database Setup

### 1. PostgreSQL Configuration

```bash
# Configure PostgreSQL
sudo -u postgres psql <<EOF
CREATE DATABASE grade_management;
CREATE USER gradeapp WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE grade_management TO gradeapp;
ALTER USER gradeapp CREATEDB;
\q
EOF

# Optimize PostgreSQL configuration
sudo tee -a /etc/postgresql/15/main/postgresql.conf <<EOF
# Performance tuning
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
EOF

sudo systemctl restart postgresql
```

### 2. Redis Configuration

```bash
# Configure Redis
sudo tee -a /etc/redis/redis.conf <<EOF
# Security
requirepass your_redis_password
bind 127.0.0.1

# Performance
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

sudo systemctl restart redis-server
```

### 3. Database Migration

```bash
# Run migrations
cd backend
alembic upgrade head

# Create initial data
python scripts/create_initial_data.py
```

## Security Configuration

### 1. Firewall Setup

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # PostgreSQL
sudo ufw deny 6379/tcp  # Redis
```

### 2. Application Security

```bash
# Set proper file permissions
sudo chown -R gradeapp:gradeapp /home/gradeapp/
sudo chmod 750 /home/gradeapp/
sudo chmod 600 /home/gradeapp/.env

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. SSL Hardening

```bash
# Add SSL configuration to nginx
sudo tee -a /etc/nginx/nginx.conf <<EOF
# SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
```

## Monitoring and Logging

### 1. Prometheus Setup

```bash
# Install Prometheus
sudo apt install prometheus

# Configure Prometheus
sudo tee /etc/prometheus/prometheus.yml > /dev/null <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'grade-management'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
EOF

sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### 2. Grafana Setup

```bash
# Install Grafana
sudo apt install -y gnupg2 curl
curl -fsSL https://apt.grafana.com/gpg.key | sudo apt-key add -
sudo add-apt-repository "deb https://apt.grafana.com stable main"
sudo apt update
sudo apt install grafana

sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 3. Log Aggregation

```bash
# Configure filebeat for log shipping
sudo apt install filebeat
sudo systemctl enable filebeat
sudo systemctl start filebeat
```

## Backup and Recovery

### 1. Automated Backup

```bash
# Create backup script
sudo tee /usr/local/bin/backup-grade-system.sh > /dev/null <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_BACKUP="$BACKUP_DIR/db_$DATE.sql"
FILES_BACKUP="$BACKUP_DIR/files_$DATE.tar.gz"

# Create database backup
pg_dump -h localhost -U gradeapp grade_management > $DB_BACKUP

# Create files backup
tar -czf $FILES_BACKUP /home/gradeapp/uploads /home/gradeapp/config

# Upload to cloud storage (optional)
# aws s3 cp $DB_BACKUP s3://your-backup-bucket/
# aws s3 cp $FILES_BACKUP s3://your-backup-bucket/

# Clean old backups
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-grade-system.sh

# Add to cron
echo "0 2 * * * /usr/local/bin/backup-grade-system.sh" | sudo crontab -
```

### 2. Recovery Procedures

```bash
# Database recovery
psql -h localhost -U gradeapp grade_management < backup_file.sql

# Files recovery
tar -xzf files_backup.tar.gz -C /
```

## Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check logs
   sudo journalctl -u gradeapp -f

   # Check configuration
   sudo -u gradeapp python -m app.main
   ```

2. **Database connection issues**
   ```bash
   # Test database connection
   psql -h localhost -U gradeapp grade_management

   # Check PostgreSQL status
   sudo systemctl status postgresql
   ```

3. **High memory usage**
   ```bash
   # Monitor memory usage
   htop

   # Check for memory leaks
   py-spy top --pid $(pgrep -f gradeapp)
   ```

4. **Performance issues**
   ```bash
   # Check slow queries
   sudo -u postgres psql grade_management -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

   # Monitor application performance
   py-spy record -o profile.svg --pid $(pgrep -f gradeapp)
   ```

### Health Checks

```bash
# Application health
curl -f http://localhost:8000/health || echo "Application down"

# Database health
pg_isready -h localhost -U gradeapp || echo "Database down"

# Redis health
redis-cli ping || echo "Redis down"
```

### Performance Tuning

1. **Database optimization**
   - Add indexes to frequently queried columns
   - Optimize slow queries
   - Configure connection pooling

2. **Application optimization**
   - Enable caching
   - Optimize API endpoints
   - Use asynchronous operations

3. **Infrastructure optimization**
   - Use load balancer
   - Enable CDN
   - Optimize Nginx configuration

## Support

For deployment support, contact:
- Email: support@university.edu.cn
- Documentation: https://docs.university.edu.cn/grade-management
- Issues: https://github.com/your-org/chinese-university-grade-management/issues