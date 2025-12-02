# Migration Guide: Bitbucket to GitHub Mono Repo

This guide provides step-by-step instructions for migrating this repository from Bitbucket to the Common Ground mono repository on GitHub.

## Prerequisites

- Git installed and configured
- Access to the Bitbucket repository
- Access to create/configure the GitHub Common-Ground repository
- GitHub CLI (`gh`) or web access to GitHub

## Step 1: Create GitHub Mono Repository

1. Create a new repository named `Common-Ground` in GitHub
   - Go to GitHub and create a new repository
   - Name: `Common-Ground`
   - Description: "Common Ground mono repository"
   - Initialize with a README (optional)

2. Clone the new repository locally:
```bash
git clone git@github.com:proactive-mgmt/Common-Ground.git
cd Common-Ground
```

3. Create initial README structure (if not already done):
```bash
cat > README.md << 'EOF'
# Common Ground

Mono repository for Common Ground projects.

## Projects

- [hope-scale-survey](hope-scale-survey/) - Automated survey distribution system
  (more projects to be added)

## Contributing

Each project maintains its own structure and documentation. See individual project READMEs for details.

**Repository**: https://github.com/proactive-mgmt/Common-Ground
EOF

git add README.md
git commit -m "Initial mono repo structure"
git push origin main
```

## Step 2: Migrate Repository with Full History

Use `git subtree` to merge the Bitbucket repo while preserving all commit history:

```bash
# From within the Common-Ground directory
# Add Bitbucket repo as a remote
git remote add hopescale-origin git@bitbucket.org:michaeljason77/cg-hopescalesurvey.git

# Fetch all commits from Bitbucket
git fetch hopescale-origin

# Merge as subtree, preserving history
# This will place all content under hope-scale-survey/ directory
git subtree add --prefix=hope-scale-survey hopescale-origin/main --squash

# If you want to preserve individual commits (not squashed), use:
# git subtree add --prefix=hope-scale-survey hopescale-origin/main

# Push to GitHub
git push origin main
```

**Note:** The `--squash` flag creates a single merge commit. Remove it if you want to preserve all individual commits.

## Step 3: Verify Migration

1. Check that all files are present:
```bash
ls -la hope-scale-survey/
```

2. Verify git history:
```bash
git log --oneline --graph --all
```

3. Check that the subtree was created correctly:
```bash
git log --oneline --prefix=hope-scale-survey
```

## Step 4: Update Bitbucket Repository

1. Commit the deprecation notice to Bitbucket:
```bash
# From the original Bitbucket repo directory (cg-hopescalesurvey)
git checkout main
git pull origin main

# The DEPRECATED.md and updated README.md should already be committed
# If not, add them:
git add DEPRECATED.md README.md
git commit -m "Add deprecation notice - repository migrated to GitHub"
git push origin main
```

2. Update Bitbucket repository settings:
   - Go to Bitbucket repository settings
   - Mark repository as archived (read-only) if desired
   - Update repository description to mention migration

## Step 5: Update References

After migration, update any external references:

1. Update CI/CD pipelines (if any)
2. Update documentation links
3. Update project management tools
4. Notify team members

## Step 6: Future Updates

To pull updates from the original Bitbucket repo (if needed before full migration):

```bash
# From Common-Ground directory
git subtree pull --prefix=hope-scale-survey hopescale-origin/main --squash
git push origin main
```

## Troubleshooting

### If subtree add fails:
- Ensure you're in the Common-Ground repository root
- Verify the remote is added correctly: `git remote -v`
- Check that the branch name is correct (may be `master` instead of `main`)

### If you need to remove and re-add:
```bash
# Remove the subtree
git rm -r hope-scale-survey
git commit -m "Remove subtree before re-adding"

# Re-add with correct settings
git subtree add --prefix=hope-scale-survey hopescale-origin/main
```

### Preserving all branches and tags:
If you need to migrate branches or tags:
```bash
# For each branch
git subtree add --prefix=hope-scale-survey hopescale-origin/[branch-name]

# For tags (requires manual process)
git fetch hopescale-origin --tags
# Then manually create tags in GitHub repo if needed
```

## Post-Migration Checklist

- [ ] All files migrated successfully
- [ ] Git history preserved
- [ ] DEPRECATED.md added to Bitbucket repo
- [ ] README.md updated in Bitbucket repo
- [ ] GitHub mono repo structure created
- [ ] All documentation references updated
- [ ] Team notified of migration
- [ ] CI/CD pipelines updated (if applicable)
- [ ] Bitbucket repo archived (optional)

