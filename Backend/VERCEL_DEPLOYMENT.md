# 🚀 PropMatch Backend - Vercel Deployment Guide

This guide will help you deploy your PropMatch FastAPI backend to Vercel.

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Environment Variables**: Have your API keys and configurations ready

## 🏗️ Deployment Steps

### Step 1: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### Step 2: Connect Your Repository

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the `Backend` folder as your project root

### Step 3: Configure Environment Variables

In your Vercel project dashboard, go to Settings → Environment Variables and add:

#### Required Variables:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

#### Optional Variables:
```env
# LangSmith Tracing
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=PropMatch-Backend

# Pinecone (if using vector search)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_pinecone_index_name

# Redis (if using caching)
REDIS_URL=your_redis_url

# Security
SECRET_KEY=your_secret_key_for_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
SEARCH_RATE_LIMIT=5/minute
EXPLANATION_RATE_LIMIT=5/minute
GENERAL_RATE_LIMIT=5/minute

# Environment
ENVIRONMENT=production
```

### Step 4: Deploy

#### Option A: Auto-Deploy via GitHub
- Push your changes to the main branch
- Vercel will automatically deploy

#### Option B: Manual Deploy via CLI
```bash
cd Backend
vercel --prod
```

## 🔧 Configuration Files Explanation

### `vercel.json`
- Configures Vercel deployment settings
- Routes all requests to the FastAPI app
- Sets Python version and memory limits

### `api/index.py`
- Entry point for Vercel serverless functions
- Imports and exports your FastAPI app
- Handles the serverless environment

### `requirements-vercel.txt`
- Optimized dependencies for serverless deployment
- Removes heavy packages not needed in production
- Reduces cold start times

## 🌐 Accessing Your Deployed API

Once deployed, your API will be available at:
- **Production URL**: `https://your-project-name.vercel.app`
- **API Documentation**: `https://your-project-name.vercel.app/docs`
- **Health Check**: `https://your-project-name.vercel.app/health`

## ⚡ Serverless Considerations

### Cold Starts
- First request may take 5-10 seconds
- Subsequent requests are fast
- Consider using Vercel Pro for better performance

### Memory and Timeout Limits
- Current configuration: 1024MB RAM, 30s timeout
- Adjust in `vercel.json` if needed
- Vercel Pro allows higher limits

### Database Connections
- Use connection pooling for better performance
- Consider serverless-friendly databases
- Supabase is already optimized for serverless

## 🔍 Troubleshooting

### Build Failures
1. Check the build logs in Vercel dashboard
2. Ensure all dependencies are in `requirements-vercel.txt`
3. Verify Python version compatibility

### Cold Start Issues
1. Reduce imports in `api/index.py`
2. Use lazy loading for heavy dependencies
3. Consider caching strategies

### CORS Issues
1. Check the allowed origins in `app/main.py`
2. Add your Vercel domain to CORS settings
3. Verify frontend URLs match exactly

### Environment Variables
1. Double-check all required variables are set
2. Ensure no trailing spaces in values
3. Use Vercel's preview deployments for testing

## 📊 Monitoring and Logs

### Viewing Logs
1. Go to your Vercel project dashboard
2. Click on a deployment
3. View "Functions" tab for logs

### Performance Monitoring
- Use Vercel Analytics (if available)
- Monitor cold start times
- Track API response times

## 🔄 CI/CD Integration

### Automatic Deployments
- Production deploys from `main` branch
- Preview deploys from pull requests
- Configure branch settings in Vercel

### Environment-Specific Deployments
```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

## 🚨 Important Notes

1. **Serverless Limitations**: Some features may need adaptation for serverless
2. **Cold Starts**: Consider implementing warming strategies for production
3. **Database Connections**: Use connection pooling to avoid connection limits
4. **File Storage**: Use external storage services (not local file system)
5. **Background Tasks**: Use external job queues for long-running tasks

## 🔗 Useful Links

- [Vercel Python Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Vercel CLI Reference](https://vercel.com/docs/cli)

## 🆘 Support

If you encounter issues:
1. Check Vercel's function logs
2. Review this deployment guide
3. Test locally first with `vercel dev`
4. Consult Vercel's documentation

Happy deploying! 🎉