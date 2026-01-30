#!/usr/bin/env python3

import os
import json
import requests
import re
import sys
from typing import Optional, Dict, Any
import google.generativeai as genai

# Get environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

# Validation
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN is not set")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY is not set")
    sys.exit(1)

if not GITHUB_EVENT_PATH:
    print("ERROR: GITHUB_EVENT_PATH is not set")
    sys.exit(1)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)


class PRAnalyzer:
    def __init__(self, github_token: str, gemini_api_key: str):
        self.github_token = github_token
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def load_github_context(self) -> Dict[str, Any]:
        """Load GitHub event context from file"""
        try:
            with open(GITHUB_EVENT_PATH, 'r') as f:
                context = json.load(f)
            return context
        except FileNotFoundError:
            print(f"ERROR: GitHub event file not found at {GITHUB_EVENT_PATH}")
            sys.exit(1)
        except json.JSONDecodeError:
            print("ERROR: Failed to parse GitHub event file")
            sys.exit(1)

    def extract_pr_details(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract PR details from GitHub context"""
        try:
            pr = context.get("pull_request")
            if not pr:
                print("ERROR: This action can only run on pull_request events")
                sys.exit(1)

            pr_details = {
                "title": pr.get("title", ""),
                "description": pr.get("body", ""),
                "number": pr.get("number"),
                "url": pr.get("html_url"),
                "repo": context.get("repository", {}).get("full_name"),
            }

            return pr_details
        except Exception as e:
            print(f"ERROR: Failed to extract PR details: {str(e)}")
            sys.exit(1)

    def extract_images_from_description(self, description: str) -> list:
        """Extract image URLs from PR description"""
        images = []
        
        # Markdown image format: ![alt](url)
        markdown_pattern = r'!\[.*?\]\((.*?)\)'
        markdown_matches = re.findall(markdown_pattern, description)
        images.extend(markdown_matches)

        # HTML image format: <img src="url">
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        html_matches = re.findall(html_pattern, description)
        images.extend(html_matches)

        return list(set(images))  # Remove duplicates

    def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                print(f"WARNING: Failed to download image from {image_url}, status: {response.status_code}")
                return None
        except Exception as e:
            print(f"WARNING: Failed to download image from {image_url}: {str(e)}")
            return None

    def analyze_with_gemini(self, pr_details: Dict[str, Any]) -> str:
        """Send PR details to Gemini AI and get analysis"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')

            # Build the prompt
            prompt = f"""You are a helpful code reviewer AI assistant. Analyze the following pull request and provide a concise, crisp response in exactly 2 lines.

Pull Request Title: {pr_details['title']}

Pull Request Description:
{pr_details['description']}

Repository: {pr_details['repo']}

Please provide:
1. A brief assessment of the PR (first line)
2. A specific suggestion or observation (second line)

Keep it short, professional, and actionable. Format as plain text, exactly 2 lines."""

            # Check if there are images to analyze
            images_to_analyze = self.extract_images_from_description(pr_details['description'])
            
            if images_to_analyze:
                print(f"Found {len(images_to_analyze)} images in PR description. Attempting to analyze them...")
                
                # Download and prepare images
                image_parts = []
                for image_url in images_to_analyze[:3]:  # Limit to 3 images
                    image_data = self.download_image(image_url)
                    if image_data:
                        # Determine image type
                        if image_url.lower().endswith('.png'):
                            mime_type = 'image/png'
                        elif image_url.lower().endswith('.gif'):
                            mime_type = 'image/gif'
                        elif image_url.lower().endswith('.webp'):
                            mime_type = 'image/webp'
                        else:
                            mime_type = 'image/jpeg'

                        image_parts.append({
                            'mime_type': mime_type,
                            'data': image_data
                        })

                if image_parts:
                    # Include images in the analysis
                    content_parts = [prompt]
                    content_parts.extend(image_parts)
                    response = model.generate_content(content_parts)
                else:
                    response = model.generate_content(prompt)
            else:
                response = model.generate_content(prompt)

            analysis = response.text.strip()
            return analysis

        except Exception as e:
            print(f"ERROR: Failed to analyze PR with Gemini: {str(e)}")
            sys.exit(1)

    def post_comment_on_pr(self, repo: str, pr_number: int, comment_body: str) -> bool:
        """Post a comment on the PR"""
        try:
            url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
            
            data = {
                "body": f"🤖 **AI Analysis:**\n\n{comment_body}"
            }

            response = requests.post(url, json=data, headers=self.headers)

            if response.status_code == 201:
                comment = response.json()
                print(f"✅ Successfully posted comment on PR #{pr_number}")
                print(f"Comment ID: {comment['id']}")
                return True
            else:
                print(f"ERROR: Failed to post comment. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"ERROR: Failed to post comment on PR: {str(e)}")
            sys.exit(1)

    def run(self):
        """Main execution flow"""
        print("=" * 60)
        print("Starting PR Analysis with Gemini AI")
        print("=" * 60)

        # Load GitHub context
        print("\n📂 Loading GitHub context...")
        context = self.load_github_context()

        # Extract PR details
        print("📝 Extracting PR details...")
        pr_details = self.extract_pr_details(context)
        print(f"   PR #{pr_details['number']}: {pr_details['title']}")
        print(f"   Repository: {pr_details['repo']}")

        # Analyze with Gemini
        print("\n🤖 Analyzing PR with Gemini AI...")
        analysis = self.analyze_with_gemini(pr_details)

        print("\n📤 Generated Analysis:")
        print("-" * 60)
        print(analysis)
        print("-" * 60)

        # Post comment on PR
        print("\n💬 Posting comment on PR...")
        success = self.post_comment_on_pr(
            pr_details['repo'],
            pr_details['number'],
            analysis
        )

        if success:
            print("\n" + "=" * 60)
            print("✅ PR Analysis and Comment Successfully Completed!")
            print("=" * 60)
        else:
            print("\n❌ Failed to post comment on PR")
            sys.exit(1)


if __name__ == "__main__":
    analyzer = PRAnalyzer(GITHUB_TOKEN, GEMINI_API_KEY)
    analyzer.run()
