# 🚀 PropMatch Deployment Guide

Complete guide to deploy your full-stack PropMatch application to production.

## 📋 **Deployment Architecture**

```
Frontend (Next.js) → Vercel
Backend (FastAPI) → Railway/Render  
Database → Supabase (already configured)
Cache → Redis Cloud (already configured)
Vector DB → Pinecone (already configured)
```

## 🎯 **Quick Deployment Steps**

### **1. Backend Deployment (Railway - Recommended)**

#### **Option A: Railway (Recommended - Free tier available)**

1. **Create Railway Account**: Go to [railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Deploy from GitHub**:
   ```bash
   # Push your code to GitHub first
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```
4. **Create New Project** → **Deploy from GitHub repo** → Select your repo
5. **Configure Environment Variables** in Railway dashboard:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   REDIS_URL=your_redis_url
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   SECRET_KEY=your_secret_key_for_jwt
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   SEARCH_RATE_LIMIT=5/minute
   EXPLANATION_RATE_LIMIT=5/minute
   GENERAL_RATE_LIMIT=5/minute
   ENVIRONMENT=production
   PORT=8000
   ```
6. **Deploy**: Railway will automatically build and deploy using the `Dockerfile`
7. **Get Backend URL**: Copy the generated URL (e.g., `https://your-app.railway.app`)

#### **Option B: Render (Alternative)**

1. **Create Render Account**: Go to [render.com](https://render.com)
2. **New Web Service** → **Connect GitHub** → Select your repo
3. **Configure**:
   - **Root Directory**: `Backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables** (same as Railway list above)
5. **Deploy**

### **2. Frontend Deployment (Vercel)**

1. **Create Vercel Account**: Go to [vercel.com](https://vercel.com)
2. **Import Project** → **GitHub** → Select your repo
3. **Configure**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `Frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. **Environment Variables**:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-app.railway.app
   ```
5. **Deploy**: Vercel will automatically build and deploy

### **3. Update CORS Settings**

After both deployments, update your backend CORS settings:

1. **Add your Vercel domain** to `ALLOWED_ORIGINS` in your backend environment:
   ```env
   ALLOWED_ORIGINS=https://your-frontend-app.vercel.app,http://localhost:3000
   ```
2. **Redeploy backend** to apply changes

## 🔧 **Local Development Setup**

### **Backend**
```bash
cd Backend
cp env.example .env
# Fill in your environment variables
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend**
```bash
cd Frontend
cp env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

## 🐳 **Docker Deployment (Alternative)**

If you prefer Docker deployment:

### **Backend Docker**
```bash
cd Backend
docker build -t propmatch-backend .
docker run -p 8000:8000 --env-file .env propmatch-backend
```

### **Full Stack Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./Backend
    ports:
      - "8000:8000"
    env_file:
      - ./Backend/.env
    
  frontend:
    build: ./Frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

## 🔐 **Environment Variables Checklist**

### **Backend (.env)**
- [ ] `SUPABASE_URL` - Your Supabase project URL
- [ ] `SUPABASE_KEY` - Your Supabase anon key
- [ ] `REDIS_URL` - Your Redis connection URL
- [ ] `OPENAI_API_KEY` - Your OpenAI API key
- [ ] `PINECONE_API_KEY` - Your Pinecone API key
- [ ] `PINECONE_ENVIRONMENT` - Your Pinecone environment
- [ ] `PINECONE_INDEX_NAME` - Your Pinecone index name
- [ ] `SECRET_KEY` - JWT secret key (generate a strong one)
- [ ] `ALLOWED_ORIGINS` - Frontend domains for CORS

### **Frontend (.env.local)**
- [ ] `NEXT_PUBLIC_API_URL` - Your deployed backend URL

## 🚨 **Security Checklist**

- [ ] **Strong SECRET_KEY**: Generate a secure JWT secret
- [ ] **CORS Configuration**: Only allow your frontend domains
- [ ] **Rate Limiting**: Configured (5 requests/minute)
- [ ] **Environment Variables**: Never commit .env files
- [ ] **HTTPS**: Both frontend and backend use HTTPS in production

## 📊 **Monitoring & Health Checks**

### **Health Check Endpoints**
- Backend: `https://your-backend.railway.app/health`
- Security: `https://your-backend.railway.app/api/v1/security/health`

### **Performance Monitoring**
- Railway/Render provide built-in monitoring
- Check logs for errors and performance issues
- Monitor Redis cache hit rates

## 🔄 **CI/CD (Automatic Deployments)**

Both Vercel and Railway support automatic deployments:

1. **Push to GitHub** → **Automatic deployment**
2. **Environment-specific branches**:
   - `main` → Production
   - `develop` → Staging (optional)

## 🆘 **Troubleshooting**

### **Common Issues**

1. **CORS Errors**: Check `ALLOWED_ORIGINS` includes your frontend domain
2. **Environment Variables**: Ensure all required vars are set
3. **Database Connection**: Verify Supabase URL and key
4. **Redis Connection**: Check Redis URL format
5. **Build Failures**: Check Python version (3.12) and dependencies

### **Debug Commands**
```bash
# Check backend health
curl https://your-backend.railway.app/health

# Check security status
curl https://your-backend.railway.app/api/v1/security/health

# Test search endpoint
curl -X POST https://your-backend.railway.app/api/v1/search/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "2 bedroom apartment", "limit": 3}'
```

## 🎉 **Post-Deployment**

1. **Test all functionality**: Search, explanations, mobile responsiveness
2. **Monitor performance**: Check response times and error rates
3. **Set up alerts**: Configure monitoring for downtime
4. **Update documentation**: Keep deployment info current

---

**🚀 Your PropMatch application is now ready for production!**

**Frontend**: `https://your-app.vercel.app`  
**Backend**: `https://your-app.railway.app`  
**API Docs**: `https://your-app.railway.app/docs` 