# Contributing to NeuralBrain-AI

## 🚀 Workflow - Feature Branches & Pull Requests (NOT Direct Commits)

**⚠️ IMPORTANT:** Never push directly to `main`. Always use feature branches and pull requests.

---

## Setup Your Environment

### 1. Clone the Repository
```bash
git clone https://github.com/Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition.git
cd NeuralBrain-AI-Hawei-Developer--Competition/NeuralBrain-AI
```

### 2. Create a Feature Branch
```bash
# Always create a NEW branch for each feature/fix
git checkout -b feature/your-feature-name

# Branch naming conventions:
# feature/add-dashboard-charts
# fix/data-explorer-error
# docs/update-readme
# refactor/optimize-queries
```

### 3. Make Your Changes
```bash
# Edit files, write code
# Test your changes locally

# Check your changes
git status
git diff
```

### 4. Commit Your Changes
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add dashboard charts

- Added Chart.js integration
- Created chart components
- Responsive on mobile"

# Commit message format:
# feat: new feature
# fix: bug fix
# docs: documentation
# refactor: code refactoring
```

### 5. Push to GitHub
```bash
# Push your feature branch (NOT main)
git push origin feature/your-feature-name
```

### 6. Create a Pull Request (PR)
1. Go to https://github.com/Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition
2. Click **"Pull requests"** tab
3. Click **"New pull request"**
4. Select your feature branch
5. Add a descriptive title and description
6. Click **"Create pull request"**

### 7. Code Review & Merge
- Wait for code review approval
- Address any requested changes
- Once approved, PR will be merged to `main`

---

## ❌ DO NOT:
- ❌ Push directly to `main`
- ❌ Use `git push origin main`
- ❌ Force-push to `main` (except repository owner for emergencies)
- ❌ Merge without review
- ❌ Commit to local `main` and push

---

## ✅ DO:
- ✅ Create a feature branch: `git checkout -b feature/name`
- ✅ Push to feature branch: `git push origin feature/name`
- ✅ Create a Pull Request on GitHub
- ✅ Wait for 1 approval
- ✅ Merge via GitHub UI

---

## 🔄 Sync With Latest Main

Before starting new work, pull the latest changes:

```bash
# Switch to main
git checkout main

# Pull latest changes
git pull origin main

# Create your new feature branch
git checkout -b feature/new-feature
```

---

## Emergency: Local Main Out of Sync

If your local `main` got corrupted:

```bash
# Reset to remote main
git fetch origin
git reset --hard origin/main
git checkout -b feature/your-feature
```

---

## Questions?
- Check existing Pull Requests for examples
- Review commit history: `git log --oneline`
- Contact: bitingojosaphat@gmail.com

---

**Thank you for contributing! 🎉**
