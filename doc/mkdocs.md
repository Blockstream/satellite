# MkDocs

A MkDocs setup is available for local development of docs and visualization
before pushing to Github Pages. Please run it as follows from the root
directory:

```bash
docker build -f doc/mkdocs.dockerfile -t blocksat-mkdocs .
```

```bash
docker run --rm -it -p 8000:8000 blocksat-mkdocs
```

Then, open http://localhost:8000 in your browser.
