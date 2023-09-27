FROM squidfunk/mkdocs-material

# Copy the docs
RUN mkdir docs/
COPY index.md /docs/docs/
COPY doc /docs/docs/

# Fix some inconsistencies with the github pages docs
RUN rm /docs/docs/README.md
RUN sed -i 's/doc\///g' /docs/docs/index.md
RUN find /docs/docs/ -type f -exec sed -i 's/..\/index.md/index.md/g' {} \;

COPY doc/mkdocs.yml .
ENTRYPOINT ["mkdocs"]
CMD ["serve", "--dev-addr=0.0.0.0:8000"]