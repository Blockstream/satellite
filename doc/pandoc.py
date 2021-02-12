#!/usr/bin/env python3
import datetime
import re
import subprocess
import tempfile

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


def remove_yaml_front_matter(text):
    """Remove the YAML front matter of a Markdown document"""
    if text[0:4] == "---\n":
        # Find where the front matter ends
        lines = text.splitlines()
        i_end = 1
        while (i_end < 10):  # front matter should use less than 10 lines
            if lines[i_end] == "---":
                break
            i_end += 1
        assert (i_end < 10), "Failed to find YAML front matter closure"

        # Remove also the extra line break after the front matter
        if (lines[i_end + 1] == ""):
            i_end += 1

        text = "\n".join(lines[(i_end + 1):])

    return text


def fix_links(concat_text, docs, title_map, absent_docs):
    """Change document links to anchor links on the concatenated text

    The original Markdown docs are linked to each other based on file
    names. However, once they are concatenated, the original file links do not
    work anymore. This function fixes the problem by changing the file links
    into the corresponding in-document anchor links, based on the document's
    title heading.

    The other problem is that not all markdown docs are included on the
    compiled pdf version. This function removes links to the docs are not
    present in the concatenated text.

    """
    # Replace all document links with the corresponding anchor link
    for doc in docs:
        # Convert title to the corresponding markdown anchor link
        anchor_link = title_map[doc].lower().replace(" ", "-")

        # Replace direct links
        original_link = "({})".format(doc)
        new_link = "(#{})".format(anchor_link)
        concat_text = concat_text.replace(original_link, new_link)

        # Fix links pointing to a particular subsection
        concat_text = concat_text.replace("({}#".format(doc), "(#")

    # Replace links to absent docs
    lines = concat_text.splitlines()
    for doc in absent_docs:
        original_link = "({})".format(doc)
        for i, line in enumerate(lines):
            if original_link in line:
                match = re.search(r"\[(.*?)\]\(" + doc + r"\)", line)
                lines[i] = line.replace(match.group(0), match.group(1))

    return "\n".join(lines)


def main():
    docs = [
        "../index.md", "hardware.md", "software.md", "s400.md", "tbs.md",
        "sat-ip.md", "sdr.md", "antenna-pointing.md", "bitcoin.md",
        "dual-satellite.md", "api.md", "docker.md", "frequency.md",
        "monitoring.md", "quick-reference.md"
    ]

    title_map = {}

    # Concatenate docs
    concat = ''
    for doc in docs:
        with open(doc) as fd:
            text = fd.read()

        # Remove YAML front matter
        text = remove_yaml_front_matter(text)

        # Keep track of page titles
        title_line = text.splitlines()[0]
        assert (title_line[:2] == "# ")
        title_map[doc] = title_line[2:]

        # Special case for the index page:
        #
        # - Remove the original Markdown title.
        # - Change the first H2 header (overview) to an H1 title. Also, change
        #   the cross-links to other documents by assuming they are on the same
        #   directory level.
        if doc == "../index.md":
            lines = text.splitlines()
            assert (lines[0] == "# Blockstream Satellite")
            assert (lines[2] == "## Overview")
            lines[2] = "# Overview"
            text = "\n".join(lines[2:])
            text = text.replace("doc/", "")

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
        # translated into LaTeX sections. Also, add some anchor links to force
        # links between documents once they are concatenated.
        concat += "\n" + text + "\n"

    # Fix some strings
    concat = concat.replace(":heavy_check_mark:", "Yes")
    concat = concat.replace(":heavy_multiplication_x:", "No")
    concat = concat.replace("This page", "This section")
    concat = concat.replace("this page", "this section")
    concat = concat.replace("antenna alignment guide",
                            "antenna alignment section")
    concat = concat.replace("Docker guide", "Docker section")
    concat = concat.replace(
        "this repository",
        "[the repository](http://github.com/Blockstream/satellite)")

    # Fix markdown links
    absent_docs = ["receiver.md"]
    concat = fix_links(concat, docs, title_map, absent_docs)

    today = datetime.datetime.now()
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(concat.encode())
        subprocess.run([
            "pandoc", fp.name, "-f", "markdown", "--pdf-engine=xelatex", "-o",
            "blocksat_manual.pdf", "-V", "title=Blockstream Satellite", "-V",
            "subtitle=User Guide", "-V", "date=" + today.strftime("%B %d, %Y"),
            "-V", "colorlinks", "--number-sections", "--toc", "--template",
            "eisvogel", "--listings", "-V", "titlepage", "-V",
            "logo=img/blockstream.png", "-V", "table-use-row-colors", "-V",
            "titlepage-rule-color=3577F8", "-V", "footnotes-pretty"
        ])


if __name__ == '__main__':
    main()
