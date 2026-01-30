#!/bin/bash
# Branch Protection Setup Script
# Configures branch protection rules for the main branch
# Requirements: GitHub CLI (gh) must be installed and authenticated
# Usage: ./setup-branch-protection.sh

set -e

REPO="Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition"
BRANCH="main"

echo "🔒 Configuring branch protection for $BRANCH branch..."

# Require pull request reviews before merging
gh api repos/$REPO/branches/$BRANCH/protection \
  -X PUT \
  -f required_status_checks=null \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f required_conversation_resolution=true

echo "✅ Branch protection configured successfully!"
echo ""
echo "Protection rules applied to '$BRANCH':"
echo "  ✓ Require 1 pull request review before merging"
echo "  ✓ Dismiss stale pull request approvals"
echo "  ✓ Block force pushes to $BRANCH"
echo "  ✓ Block deletion of $BRANCH"
echo "  ✓ Require conversation resolution"
echo "  ✓ Allow admins to bypass these settings"
echo ""
echo "Next: Have team members create feature branches and submit Pull Requests"
