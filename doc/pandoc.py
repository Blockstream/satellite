import datetime
import re
import subprocess
import tempfile

abstract = """The Blockstream Satellite network broadcasts the Bitcoin blockchain
worldwide 24/7 for free, protecting against network interruptions and providing
areas without reliable internet connections with the opportunity to use
Bitcoin. You can join this network by running your own Blockstream Satellite
receiver node. This document provides detailed guidance for all the hardware
options, software components, and instructions to assemble a satellite receive
setup."""

footnote_map = {}


def convert_footnotes(text, doc):
    """Convert footnotes from github-flavored markdown into extended markdown

    The extended markdown format provides a more specific syntax for footnotes,
    which pandoc can process and convert into LaTeX footnotes.

    This function assumes each document has a unique set of footnotes, and that
    multiple docs can adopt the same footnote numbering. It keeps a global
    record of footnotes and increases the footnote number such that the
    concatenated text does not have duplicate footnotes.

    """
    lines = text.splitlines()
    footnote = None

    for i, line in enumerate(lines):
        if "<sup>" in line:
            footnote = re.search(r"<sup>(.*?)</sup>", line).group(1)

            if doc not in footnote_map:
                footnote_map[doc] = {}

            # Assign a global footnote number
            if footnote in footnote_map[doc]:
                i_footnote = footnote_map[doc][footnote]['idx']
            else:
                i_footnote = sum([len(x) for x in footnote_map.values()]) + 1
                footnote_map[doc][footnote] = {
                    'idx': i_footnote,
                    'ref_missing': True
                }

            if footnote_map[doc][footnote]['ref_missing']:
                # Footnote reference (without colon)
                lines[i] = line.replace("<sup>" + footnote + "</sup>",
                                        "[^{}]".format(i_footnote))
                footnote_map[doc][footnote]['ref_missing'] = False
            else:
                # Footnote definition (with colon)
                lines[i] = line.replace("<sup>" + footnote + "</sup>",
                                        "[^{}]:".format(i_footnote))
    return "\n".join(lines)


def main():
    docs = [
        "intro.md", "frequency.md", "hardware.md", "s400.md", "tbs.md",
        "sat-ip.md", "sdr.md", "antenna-pointing.md", "bitcoin.md",
        "dual-satellite.md", "api.md", "docker.md", "quick-reference.md"
    ]

    # Concatenate docs
    concat = ''
    for doc in docs:
        with open(doc) as fd:
            text = fd.read()

        # Remove ToC
        text = re.sub(r'<!-- markdown-toc start [\s\S]+?markdown-toc end -->',
                      '', text)

        # Remove internal links
        lines = text.splitlines()
        if "Prev:" in lines[-1]:
            text = "\n".join(lines[:-3])

        # Convert footnotes
        text = convert_footnotes(text, doc)

        # Make sure there are line breaks between documents so that they are
        # translated into LaTeX sections
        concat += "\n" + text + "\n"

    # Fix some strings
    concat = concat.replace(":heavy_check_mark:", "Yes")
    concat = concat.replace(":heavy_multiplication_x:", "No")
    concat = concat.replace("This page", "This section")
    concat = concat.replace("this page", "this section")

    today = datetime.datetime.now()
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(concat.encode())
        subprocess.run([
            "pandoc", fp.name, "-f", "markdown", "--pdf-engine=xelatex", "-o",
            "blocksat_manual.pdf", "-V", "title=Blockstream Satellite", "-V",
            "subtitle=User Guide", "-V", "date=" + today.strftime("%B %d, %Y"),
            "-V", "abstract=" + abstract, "-V", "colorlinks",
            "--number-sections", "--toc", "--template", "eisvogel",
            "--listings", "-V", "titlepage", "-V", "logo=img/logo_blks.png",
            "-V", "table-use-row-colors", "-V", "titlepage-rule-color=3577F8",
            "-V", "footnotes-pretty"
        ])


if __name__ == '__main__':
    main()
