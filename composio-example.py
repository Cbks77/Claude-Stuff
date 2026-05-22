"""
Composio + Claude Code Integration Example
Workspace: curtisbrooks77_workspace
API Key: uak_75L-MQdUUANwBscpDuWo

This file demonstrates what you can build with Composio.
Run this after running composio-setup.sh on your local machine.
"""

# ============================================================
# 1. BASIC SETUP
# ============================================================
from composio import ComposioToolSet, App, Action
from anthropic import Anthropic

COMPOSIO_API_KEY = "uak_75L-MQdUUANwBscpDuWo"

toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
client = Anthropic()

# ============================================================
# 2. USE WITH CLAUDE - GitHub Automation Example
# ============================================================
def github_agent():
    """
    AI agent that can interact with GitHub via Composio.
    Requires: composio add github (run once to connect your account)
    """
    tools = toolset.get_tools(apps=[App.GITHUB])

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=tools,
        messages=[{
            "role": "user",
            "content": "List my GitHub repositories and find any open pull requests."
        }]
    )
    return response


# ============================================================
# 3. GMAIL AUTOMATION EXAMPLE
# ============================================================
def gmail_agent():
    """
    AI agent that can read and send emails via Composio.
    Requires: composio add gmail
    """
    tools = toolset.get_tools(apps=[App.GMAIL])

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=tools,
        messages=[{
            "role": "user",
            "content": "Check my unread emails from the last 24 hours and summarize them."
        }]
    )
    return response


# ============================================================
# 4. SLACK AUTOMATION EXAMPLE
# ============================================================
def slack_agent():
    """
    AI agent that can post messages to Slack via Composio.
    Requires: composio add slack
    """
    tools = toolset.get_tools(apps=[App.SLACK])

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=tools,
        messages=[{
            "role": "user",
            "content": "Post a daily standup reminder to the #general channel."
        }]
    )
    return response


# ============================================================
# 5. MULTI-APP WORKFLOW EXAMPLE
# ============================================================
def multi_app_agent():
    """
    Agent that orchestrates multiple services at once.
    Create GitHub issue → Notify Slack → Log to Notion
    """
    tools = toolset.get_tools(apps=[
        App.GITHUB,
        App.SLACK,
        App.NOTION,
    ])

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=tools,
        messages=[{
            "role": "user",
            "content": (
                "Create a GitHub issue titled 'Bug: Login page crash on mobile', "
                "then notify #dev-team on Slack with the issue link, "
                "and log it in my Notion bug tracker."
            )
        }]
    )
    return response


# ============================================================
# 6. LIST ALL AVAILABLE ACTIONS
# ============================================================
def list_actions_for_app(app_name: str):
    """Show all actions available for a given app."""
    actions = toolset.get_tools(apps=[app_name])
    print(f"\n📦 Actions for {app_name}:")
    for action in actions:
        print(f"  - {action.get('function', {}).get('name', 'unknown')}")


if __name__ == "__main__":
    print("✅ Composio SDK loaded successfully")
    print("📋 Available capabilities:")
    print("   - github_agent():     GitHub repos, PRs, issues")
    print("   - gmail_agent():      Read/send emails")
    print("   - slack_agent():      Post Slack messages")
    print("   - multi_app_agent():  Orchestrate multiple services")
    print("")
    print("👉 First connect an app: composio add github")
