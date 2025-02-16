git diff --name-only | grep -E '^app/.*\.py$' | while read file; do
    echo "Linting $file"
    isort "$file"
    black "$file"
done