# LangSmith Tracing Setup

LangSmith is now integrated into PropMatch for AI observability and tracing. This allows you to monitor and debug your AI calls in real-time.

## Quick Setup

1. **Get your LangSmith API key**:
   - Go to [LangSmith Settings](https://smith.langchain.com/settings)
   - Click "Create API Key"
   - Copy your API key

2. **Add to your `.env` file**:
   ```bash
   LANGSMITH_API_KEY=your_langsmith_api_key_here
   LANGSMITH_TRACING=true
   LANGSMITH_PROJECT=PropMatch-Backend
   ```

3. **That's it!** Your AI calls will now be traced automatically.

## What Gets Traced

- **AI Re-ranking Service**: All property ranking calls with GPT-4o-mini
- **Explanation Service**: Property explanation generation
- **Search operations**: Complete search and rerank workflows

## Viewing Traces

Visit your LangSmith project at:
https://smith.langchain.com/projects/PropMatch-Backend

## Health Check

Check if LangSmith is working by visiting:
- `/health` - Shows LangSmith status in the main health endpoint
- `/api/v1/test/health/` - Test endpoints with LangSmith status

## Features

- ✅ **Automatic tracing** of all OpenAI calls
- ✅ **Function-level tracing** with `@traceable` decorators
- ✅ **Token usage tracking** and performance metrics
- ✅ **Error monitoring** and debugging
- ✅ **Zero code changes** required for basic tracing

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGSMITH_API_KEY` | - | Your LangSmith API key (required) |
| `LANGSMITH_TRACING` | `true` | Enable/disable tracing |
| `LANGSMITH_PROJECT` | `PropMatch-Backend` | Project name in LangSmith |

## Troubleshooting

If tracing isn't working:

1. Check your API key is correct
2. Ensure `LANGSMITH_TRACING=true`
3. Check the `/health` endpoint for status
4. Look for LangSmith initialization logs on startup

## Benefits

- **Debug AI issues** faster with detailed traces
- **Monitor performance** and token usage
- **Track user interactions** with AI features
- **Optimize prompts** based on real usage data
- **Detect errors** and edge cases in AI responses 