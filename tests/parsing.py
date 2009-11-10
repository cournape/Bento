import os

from nose.tools import \
    assert_equal

from toydist.cabal_parser.cabal_parser import \
    parse

def test_metadata():
    meta_ref = {
        "name": "foo",
        "version": "1.0",
        "summary": "A summary",
        "author": "John Doe",
        "authoremail": "john@doe.com",
        "maintainer": "John DoeDoe",
        "maintaineremail": "john@doedoe.com",
        "license": "BSD",
        "platforms": ["any"]
    }

    meta_str = """\
Name: foo
Version: 1.0
Summary: A summary
Description:     
    Some more complete description of the package, spread over severala
    indented lines
Author: John Doe
AuthorEmail: john@doe.com
Maintainer: John DoeDoe
MaintainerEmail: john@doedoe.com
License: BSD
Platforms: any
"""

    parsed = parse(meta_str.splitlines())
    for k in meta_ref:
        assert_equal(parsed[k], meta_ref[k])

# XXX: known failure
#def test_url_metadata():
#    meta_ref = {
#        "name": "foo",
#        "summary": "A summary",
#        "downloadurl": "http://www.example.com",
#    }
#
#    meta_str = """\
#Name: foo
#Summary: A summary
#DownloadUrl: http://www.example.com
#"""
#
#    parsed = parse(meta_str.splitlines())
#    for k in meta_ref:
#        assert_equal(parsed[k], meta_ref[k])
