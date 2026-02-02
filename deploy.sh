#!/usr/bin/env sh

# abort on errors
set -e

# clean previous build to avoid git conflicts
rm -rf dist

# build
echo "Building site..."
npm run build

# navigate into the build output directory
cd dist

# place .nojekyll to bypass Jekyll processing
echo > .nojekyll

echo "Initializing deployment..."
git init
git checkout -b main
git add -A
git commit -m 'deploy'

# deploying to https://<USERNAME>.github.io/<REPO>
echo "Pushing to gh-pages..."
git push -f https://github.com/SnipersRUs/SnipersRUs.git main:gh-pages

cd -
