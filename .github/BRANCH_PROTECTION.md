# 🔒 Branch Protection Setup Instructions

## What This Does
Prevents direct pushes to `main` and requires all changes to go through Pull Requests with proper review.

---

## Option 1: GitHub CLI (Automated - Recommended)

### Prerequisites
```bash
# Install GitHub CLI if not already installed
brew install gh  # macOS
# or sudo apt-get install gh  # Ubuntu/Linux
# or Download from https://cli.github.com

# Authenticate
gh auth login
```

### Run Setup Script
```bash
cd /path/to/repo
chmod +x .github/scripts/setup-branch-protection.sh
.github/scripts/setup-branch-protection.sh
```

---

## Option 2: Manual GitHub UI Setup

1. Go to your repository on GitHub
2. **Settings** → **Branches**
3. Click **Add rule** under "Branch protection rules"
4. For branch name, enter: `main`
5. Check these boxes:
   - ✅ **Require a pull request before merging**
     - Require approvals: **1**
     - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ **Require branches to be up to date before merging**
   - ✅ **Require status checks to pass before merging**
   - ✅ **Restrict who can push to matching branches**
   - ✅ **Allow force pushes**: None (default)
   - ✅ **Allow deletions**: Unchecked

6. Click **Create**

---

## Option 3: GitHub REST API

```bash
REPO="Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition"
BRANCH="main"

gh api repos/$REPO/branches/$BRANCH/protection \
  -X PUT \
  -f required_status_checks=null \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f required_conversation_resolution=true
```

---

## Verify Protection is Enabled

```bash
REPO="Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition"
BRANCH="main"

gh api repos/$REPO/branches/$BRANCH/protection
```

Should return the protection settings.

---

## What's Protected

Once enabled, your `main` branch will:
- ❌ Reject direct pushes
- ✅ Require pull requests for all changes
- ✅ Require 1 approval before merging
- ✅ Auto-dismiss old approvals when new commits are pushed
- ❌ Block force-pushes from all users
- ❌ Block branch deletion

---

## For Team Members

After branch protection is enabled:

```bash
# ❌ This will FAIL (good!)
git push origin main

# ✅ This is the correct workflow
git checkout -b feature/my-feature
git push origin feature/my-feature
# Then create PR on GitHub for review
```

---

## Emergency: Owner Override

**Repository owner only** can bypass protection if absolutely necessary:

Go to **Settings** → **Branches** → **Branch protection rules for main** → Enable **"Allow force pushes"** → Choose **"Administrators"** (temporarily, then disable after)

---

## Support
- Read [CONTRIBUTING.md](../../CONTRIBUTING.md) for workflow details
- Check [GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
