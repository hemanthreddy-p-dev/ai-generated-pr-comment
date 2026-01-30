# Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            GitHub Repository                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  When PR is opened/edited:                                  │
│  ├─ GitHub sends event to GitHub Actions                    │
│  └─ Triggers workflow: .github/workflows/pr-analysis.yml    │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│     GitHub Actions Runner (ubuntu-latest)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Steps:                                                     │
│  1. Checkout code                                           │
│  2. Run action with inputs:                                 │
│     - github-token: ${{ secrets.GITHUB_TOKEN }}             │
│     - gemini-api-key: ${{ secrets.GEMINI_API_KEY }}         │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          Docker Container (Starts)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Base Image: python:3.11-slim                               │
│  ├─ System packages: curl, git                              │
│  ├─ Python packages: google-generativeai, requests          │
│  └─ Working directory: /action                              │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│        entrypoint.sh (Bash Script)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Receives 2 arguments:                                      │
│  1. GITHUB_TOKEN                                            │
│  2. GEMINI_API_KEY                                          │
│                                                             │
│  Actions:                                                   │
│  ├─ Export as environment variables                         │
│  └─ Execute: python /action/analyze_pr.py                   │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│     analyze_pr.py (Main Python Script)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRAnalyzer Class Flow:                                     │
│                                                             │
│  1. load_github_context()                                   │
│     └─ Read: $GITHUB_EVENT_PATH                             │
│        ↓ JSON file with PR event data                       │ 
│                                                             │
│  2. extract_pr_details()                                    │
│     ├─ title: String                                        │
│     ├─ description: String (may contain images)             │
│     ├─ number: Integer (PR #)                               │
│     ├─ url: GitHub PR URL                                   │
│     └─ repo: owner/repo format                              │
│                                                             │
│  3. extract_images_from_description()                       │
│     ├─ Regex 1: ![alt](url) [Markdown]                      │
│     ├─ Regex 2: <img src="url"> [HTML]                      │
│     └─ Returns: List of image URLs                          │
│                                                             | 
│  4. download_image() [For each image]                       │
│     ├─ HTTP GET to image URL                                │
│     └─ Returns: Binary image data                           │
│                                                             │
│  5. analyze_with_gemini()                                   │
│     ├─ Create prompt with PR details                        │
│     ├─ Add images as binary data                            │
│     ├─ Call: genai.GenerativeModel('gemini-2.0-flash')      │
│     └─ Returns: 2-line text analysis                        │
│                                                             │
│  6. post_comment_on_pr()                                    │
│     ├─ API Endpoint: /repos/{repo}/issues/{#}/comments      │
│     ├─ Method: POST                                         │
│     ├─ Headers: Authorization: token {GITHUB_TOKEN}         |
│     └─ Body: {"body": "🤖 AI Analysis:\n..."}                                    
│                                                             │
│  7. run() [Orchestrator]                                    │
│     └─ Calls all above methods in sequence                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
GitHub Event (JSON)
{
  "pull_request": {
    "number": 42,
    "title": "Add feature X",
    "body": "Description with ![image](url)",
    "html_url": "https://github.com/user/repo/pull/42"
  },
  "repository": {
    "full_name": "user/repo"
  }
}
│
└─→ load_github_context()
    │
    └─→ extract_pr_details()
        {
          "title": "Add feature X",
          "description": "Description with ![image](url)",
          "number": 42,
          "url": "https://github.com/user/repo/pull/42",
          "repo": "user/repo"
        }
        │
        └─→ extract_images_from_description()
            │
            └─→ ["https://example.com/image.png"]
                │
                └─→ download_image()
                    │
                    └─→ [Binary PNG data]
                        │
                        └─→ analyze_with_gemini()
                            {
                              "prompt": "Title: Add feature X\nDescription: ...\n[Image]",
                              "model": "gemini-2.0-flash"
                            }
                            │
                            └─→ Gemini API
                                │
                                └─→ "Well-designed feature with clean code.\nConsider adding error handling."
                                    │
                                    └─→ post_comment_on_pr()
                                        │
                                        └─→ GitHub API POST /repos/user/repo/issues/42/comments
                                            │
                                            └─→ Comment posted ✅
```

## Class Structure

```
PRAnalyzer
│
├── Attributes:
│   ├── github_token: str
│   └── headers: dict {Authorization, Accept, X-GitHub-Api-Version}
│
├── Methods:
│   ├── __init__(github_token, gemini_api_key)
│   │   └─ Initialize with credentials
│   │
│   ├── load_github_context() → Dict[str, Any]
│   │   └─ Read $GITHUB_EVENT_PATH file
│   │
│   ├── extract_pr_details(context) → Dict[str, Any]
│   │   └─ Parse PR info from context
│   │
│   ├── extract_images_from_description(description) → List[str]
│   │   ├─ Find Markdown images: ![alt](url)
│   │   └─ Find HTML images: <img src="url">
│   │
│   ├── download_image(image_url) → Optional[bytes]
│   │   └─ HTTP GET with timeout
│   │
│   ├── analyze_with_gemini(pr_details) → str
│   │   ├─ Build prompt from PR details
│   │   ├─ Include downloaded images
│   │   └─ Call Gemini API
│   │
│   ├── post_comment_on_pr(repo, pr_number, comment) → bool
│   │   └─ POST to GitHub API
│   │
│   └── run()
│       └─ Orchestrate full workflow
│
└── Usage:
    analyzer = PRAnalyzer(token, key)
    analyzer.run()
```

## Sequence Diagram

```
GitHub       Runner      Container    Python Script    GitHub API    Gemini API
  │             │             │              │              │            │
  │ PR Event    │             │              │              │            │
  ├────────────→│             │              │              │            │
  │             │ Build       │              │              │            │
  │             │ Container   │              │              │            │
  │             ├────────────→│              │              │            │
  │             │             │ Run          │              │            │
  │             │             │ entrypoint   │              │            │
  │             │             ├─────────────→│              │            │
  │             │             │   Run        │              │            │
  │             │             │   analyze_pr │              │            │
  │             │             │              │              │            │
  │             │             │  Load Context│              │            │
  │             │             │←─ GITHUB_    │              │            │
  │             │             │   EVENT_PATH │              │            │
  │             │             │              │              │            │
  │             │             │  Extract PR  │              │            │
  │             │             │  Details     │              │            │
  │             │             │              │              │            │
  │             │             │  Find Images │              │            │
  │             │             │  Download    │              │            │
  │             │             │  Images      │              │            │
  │             │             │              │              │            │
  │             │             │  Send to AI  │              │            │
  │             │             │              ├─────────────────────────→ │
  │             │             │              │   PR + Images + Prompt    │
  │             │             │              │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─    │
  │             │             │              │   2-Line Analysis         │
  │             │             │              │                           │
  │             │             │  Post Comment│              │            │
  │             │             │              ├─────────────→│            │
  │             │             │              │   POST /comments          │
  │             │             │              │←─────────────│------------|            
  │             │             │              │   201 Created             │
  │             │             │              │                           │
  │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ------- │
  │  Comment Posted on PR                                             
```

## File Dependencies

```
action.yml
  ├─ References: Dockerfile
  │   Dockerfile
  │   ├─ COPY requirements.txt
  │   │   requirements.txt
  │   │   ├─ google-generativeai
  │   │   ├─ requests
  │   │   └─ python-dotenv
  │   │
  │   ├─ COPY entrypoint.sh
  │   │   entrypoint.sh
  │   │   └─ Calls: analyze_pr.py
  │   │       analyze_pr.py
  │   │       ├─ Uses: google.generativeai
  │   │       ├─ Uses: requests
  │   │       └─ Uses: os, json, re, sys
  │   │
  │   └─ COPY analyze_pr.py
  │
  └─ Passes inputs to: entrypoint.sh
```

## Environment Variables Flow

```
action.yml inputs
  ├─ inputs.github-token
  │   └─ ${{ secrets.GITHUB_TOKEN }}
  │
  └─ inputs.gemini-api-key
      └─ ${{ secrets.GEMINI_API_KEY }}
         │
         └─ Passed to entrypoint.sh as arguments ($1, $2)
            │
            └─ entrypoint.sh exports to environment
               │
               ├─ export GITHUB_TOKEN="$1"
               └─ export GEMINI_API_KEY="$2"
                  │
                  └─ analyze_pr.py reads via os.getenv()
                     │
                     ├─ PRAnalyzer(GITHUB_TOKEN, GEMINI_API_KEY)
                     │
                     ├─ headers["Authorization"] = f"token {GITHUB_TOKEN}"
                     │
                     └─ genai.configure(api_key=GEMINI_API_KEY)

Also provided by GitHub Actions:
  │
  └─ export GITHUB_EVENT_PATH="/github/workflow/event.json"
     │
     └─ analyze_pr.py reads via os.getenv("GITHUB_EVENT_PATH")
        │
        └─ load_github_context() opens and parses JSON
```

## Error Handling Flow

```
Start
│
├─ Check GITHUB_TOKEN env variable
│  ├─ ✅ Present: Continue
│  └─ ❌ Missing: Exit with error
│
├─ Check GEMINI_API_KEY env variable
│  ├─ ✅ Present: Continue
│  └─ ❌ Missing: Exit with error
│
├─ Check GITHUB_EVENT_PATH env variable
│  ├─ ✅ Present: Continue
│  └─ ❌ Missing: Exit with error
│
├─ Load GitHub event file
│  ├─ ✅ File exists: Parse JSON
│  └─ ❌ File not found: Exit with error
│
├─ Extract PR details
│  ├─ ✅ PR event found: Continue
│  └─ ❌ Not PR event: Exit with error
│
├─ Find and download images
│  ├─ ✅ Images found: Download
│  ├─ ⚠️  Download fails: Skip image, continue
│  └─ ✅ No images: Continue without them
│
├─ Call Gemini API
│  ├─ ✅ Success: Get 2-line response
│  └─ ❌ API error: Exit with error
│
└─ Post comment on PR
   ├─ ✅ Comment posted (201): Success
   └─ ❌ API error: Exit with error
```
