# AI Generated PR Comment with Gemini

A GitHub Action that automatically analyzes pull requests using Google Gemini AI and posts intelligent, concise comments.

## Features

- ✨ Extracts PR title, description, and images
- 🤖 Analyzes with Google Gemini AI
- 💬 Posts 2-line intelligent comments on PRs
- 🖼️ Supports images in PR descriptions (Markdown & HTML)
- 🔐 Secure token-based authentication

## Quick Setup

1. Add to your `.github/workflows/pr-analysis.yml`:

```yaml
on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: hemanthreddy-p-dev/ai-generated-pr-comment@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
```

2. Add `GEMINI_API_KEY` to Repository Secrets (get from [Google AI Studio](https://aistudio.google.com))

## How It Works

### Architecture Flow

```
GitHub PR Event → entrypoint.sh (Bash) → analyze_pr.py (Python)
                                              ├── Load GitHub context
                                              ├── Extract PR details & images
                                              ├── Download images
                                              ├── Gemini AI analysis
                                              └── Post comment on PR
```

### Implementation Details

**action.yml**
- Defines action metadata and input parameters
- Specifies Docker container type
- Passes github-token & gemini-api-key to entrypoint

**Dockerfile**
- Python 3.11 slim base image
- Installs system dependencies
- Sets working directory and copies files
- Makes entrypoint.sh executable

**entrypoint.sh**
- Receives tokens from action.yml
- Exports to environment variables
- Calls analyze_pr.py

**analyze_pr.py** (Core Logic)
- `PRAnalyzer` class with these methods:
  - `load_github_context()` - Reads GitHub event from $GITHUB_EVENT_PATH
  - `extract_pr_details()` - Gets PR number, title, description, URL
  - `extract_images_from_description()` - Uses regex to find images:
    - Markdown format: `![alt](url)`
    - HTML format: `<img src="url">`
  - `download_image()` - Fetches image files over HTTP
  - `analyze_with_gemini()` - Sends PR data + images to Gemini API
  - `post_comment_on_pr()` - Posts analysis via GitHub API
  - `run()` - Orchestrates entire workflow

**requirements.txt**
- `google-generativeai` - Gemini API client
- `requests` - HTTP requests (GitHub API, image downloads)
- `python-dotenv` - Environment variable handling

## Step-by-Step Execution

1. **Trigger Event**: PR opened/edited/synchronized
2. **Container Start**: Dockerfile builds environment
3. **entrypoint.sh** runs with tokens passed as arguments
4. **analyze_pr.py** loads GitHub event context
5. **Extract** PR details from event JSON
6. **Find Images** using regex patterns in description
7. **Download** image files (max 3 images)
8. **Send to Gemini** with full PR context + image data
9. **Receive** 2-line analysis from AI
10. **Post Comment** via GitHub REST API

## Example Workflow

**PR Title:** "Implement user authentication"
**Description:**
```
Adds OAuth2 with JWT tokens.
![auth-diagram](https://example.com/diagram.png)
```

**Generated Comment:**
```
🤖 **AI Analysis:**

Well-implemented OAuth2 with proper security practices.
Add unit tests for token expiration and refresh scenarios.
```

## Image Support

The action automatically:
1. Detects images in PR description
2. Downloads images from URLs
3. Sends images to Gemini along with text
4. Includes image context in analysis

## Security Best Practices

- ✅ Use `secrets.GITHUB_TOKEN` (GitHub-provided, safe)
- ✅ Add `GEMINI_API_KEY` to repository secrets
- ✅ Never commit API keys to repository
- ✅ Limit workflow permissions: `pull-requests: write`
- ✅ Monitor Gemini API usage in Google Cloud Console

## Repository Structure

```
ai-generated-pr-comment/
├── action.yml          # Action definition
├── Dockerfile          # Container build
├── entrypoint.sh       # Bash entry point
├── analyze_pr.py       # Main Python logic
├── requirements.txt    # Dependencies
└── README.md           # Documentation
```

## Troubleshooting

- **Images not analyzed?** Check if publicly accessible
- **API errors?** Verify Gemini API key validity
- **No comment posted?** Check GitHub token permissions