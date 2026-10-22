> Publish the extracted release ZIP, not the private working directory. See [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md).

# Put the project on GitHub

The prepared archive is `runtime/release/fundamental-valuation-workbench.zip`.
Extract it into an empty directory and use that directory as your repository root.
Do not upload the private `valuation-workbench` working directory.
Do not upload the parent watcher directory or the contents of `runtime/`.

From the extracted directory:

```sh
python -m unittest discover -s tests -v
python scripts/replay_example.py
python run.py
```

Use GitHub's new repository flow to create an empty repository. Then, after reviewing
the source, blank company templates and synthetic examples, publish with Git or GitHub Desktop. A Git
sequence is shown below; replace the placeholder remote with your repository URL.

```sh
git init
git add .
git status
git commit -m "Build offline fundamental valuation workbench"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fundamental-valuation-workbench.git
git push -u origin main
```

Suggested description: **Offline Philippine equity valuation workbench with editable
company data, industry-aware methods, sensitivity analysis and reproducible scenarios.**

The README links to screenshots and a portfolio demonstration. Replace the example
thesis with your own reviewed work if you want to demonstrate your investing approach.
Personal saved scenarios and file backups are ignored by default; deliberately copy
only suitable examples into `examples/` if you want them published.

The owner selected the MIT license for original code. Source financial documents remain linked to their
publishers; downloaded figures, report excerpts and PDFs are excluded from this archive.

GitHub hosts the code. This app's file-saving backend runs locally, so uploading the
repository does not create a live GitHub Pages application. Employers can run it
with Python or inspect the walkthrough, screenshots, example and tests.
