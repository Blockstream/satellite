#!/bin/sh
set -xe

# LaTeX dependencies
tlmgr update --self
tlmgr install adjustbox \
	  babel-german \
	  background \
	  bidi \
	  collectbox \
	  csquotes \
	  everypage \
	  filehook \
	  footmisc \
	  footnotebackref \
	  framed \
	  fvextra \
	  koma-script \
	  letltxmacro \
	  ly1 \
	  mdframed \
	  mweights \
	  needspace \
	  pagecolor \
	  sourcecodepro \
	  sourcesanspro \
	  titling \
	  ucharcat \
	  ulem \
	  unicode-math \
	  upquote \
	  xecjk \
	  xurl \
	  zref

# Pandoc template
TEMPLATE=Eisvogel-2.0.0.tar.gz
TEMPLATE_DIR=/root/.local/share/pandoc/templates
TEMPLATE_URL=https://github.com/Wandmalfarbe/pandoc-latex-template/releases/download/v2.0.0/$TEMPLATE

mkdir -p $TEMPLATE_DIR
wget $TEMPLATE_URL -P $TEMPLATE_DIR
tar -xzf $TEMPLATE_DIR/$TEMPLATE -C $TEMPLATE_DIR
