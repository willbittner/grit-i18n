#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Unit tests for base.Node functionality (as used in various subclasses)'''


import os
import sys
if __name__ == '__main__':
  sys.path[0] = os.path.abspath(os.path.join(sys.path[0], '../..'))

import StringIO
import unittest

from grit import grd_reader
from grit import util
from grit.node import base
from grit.node import message


def MakePlaceholder(phname='BINGO'):
  ph = message.PhNode()
  ph.StartParsing(u'ph', None)
  ph.HandleAttribute(u'name', phname)
  ph.AppendContent(u'bongo')
  ph.EndParsing()
  return ph


class NodeUnittest(unittest.TestCase):
  def testWhitespaceHandling(self):
    # We test using the Message node type.
    node = message.MessageNode()
    node.StartParsing(u'hello', None)
    node.HandleAttribute(u'name', u'bla')
    node.AppendContent(u" '''  two spaces  ")
    node.EndParsing()
    self.failUnless(node.GetCdata() == u'  two spaces')

    node = message.MessageNode()
    node.StartParsing(u'message', None)
    node.HandleAttribute(u'name', u'bla')
    node.AppendContent(u"  two spaces  '''  ")
    node.EndParsing()
    self.failUnless(node.GetCdata() == u'two spaces  ')

  def testWhitespaceHandlingWithChildren(self):
    # We test using the Message node type.
    node = message.MessageNode()
    node.StartParsing(u'message', None)
    node.HandleAttribute(u'name', u'bla')
    node.AppendContent(u" '''  two spaces  ")
    node.AddChild(MakePlaceholder())
    node.AppendContent(u' space before and after ')
    node.AddChild(MakePlaceholder('BONGO'))
    node.AppendContent(u" space before two after  '''")
    node.EndParsing()
    self.failUnless(node.mixed_content[0] == u'  two spaces  ')
    self.failUnless(node.mixed_content[2] == u' space before and after ')
    self.failUnless(node.mixed_content[-1] == u' space before two after  ')

  def testXmlFormatMixedContent(self):
    # Again test using the Message node type, because it is the only mixed
    # content node.
    node = message.MessageNode()
    node.StartParsing(u'message', None)
    node.HandleAttribute(u'name', u'name')
    node.AppendContent(u'Hello <young> ')

    ph = message.PhNode()
    ph.StartParsing(u'ph', None)
    ph.HandleAttribute(u'name', u'USERNAME')
    ph.AppendContent(u'$1')
    ex = message.ExNode()
    ex.StartParsing(u'ex', None)
    ex.AppendContent(u'Joi')
    ex.EndParsing()
    ph.AddChild(ex)
    ph.EndParsing()

    node.AddChild(ph)
    node.EndParsing()

    non_indented_xml = node.Format(node)
    self.failUnless(non_indented_xml == u'<message name="name">\n  Hello '
                    u'&lt;young&gt; <ph name="USERNAME">$1<ex>Joi</ex></ph>'
                    u'\n</message>')

    indented_xml = node.FormatXml(u'  ')
    self.failUnless(indented_xml == u'  <message name="name">\n    Hello '
                    u'&lt;young&gt; <ph name="USERNAME">$1<ex>Joi</ex></ph>'
                    u'\n  </message>')

  def testXmlFormatMixedContentWithLeadingWhitespace(self):
    # Again test using the Message node type, because it is the only mixed
    # content node.
    node = message.MessageNode()
    node.StartParsing(u'message', None)
    node.HandleAttribute(u'name', u'name')
    node.AppendContent(u"'''   Hello <young> ")

    ph = message.PhNode()
    ph.StartParsing(u'ph', None)
    ph.HandleAttribute(u'name', u'USERNAME')
    ph.AppendContent(u'$1')
    ex = message.ExNode()
    ex.StartParsing(u'ex', None)
    ex.AppendContent(u'Joi')
    ex.EndParsing()
    ph.AddChild(ex)
    ph.EndParsing()

    node.AddChild(ph)
    node.AppendContent(u" yessiree '''")
    node.EndParsing()

    non_indented_xml = node.Format(node)
    self.failUnless(non_indented_xml ==
                    u"<message name=\"name\">\n  '''   Hello"
                    u' &lt;young&gt; <ph name="USERNAME">$1<ex>Joi</ex></ph>'
                    u" yessiree '''\n</message>")

    indented_xml = node.FormatXml(u'  ')
    self.failUnless(indented_xml ==
                    u"  <message name=\"name\">\n    '''   Hello"
                    u' &lt;young&gt; <ph name="USERNAME">$1<ex>Joi</ex></ph>'
                    u" yessiree '''\n  </message>")

    self.failUnless(node.GetNodeById('name'))

  def testXmlFormatContentWithEntities(self):
    '''Tests a bug where &nbsp; would not be escaped correctly.'''
    from grit import tclib
    msg_node = message.MessageNode.Construct(None, tclib.Message(
      text = 'BEGIN_BOLDHelloWHITESPACEthere!END_BOLD Bingo!',
      placeholders = [
        tclib.Placeholder('BEGIN_BOLD', '<b>', 'bla'),
        tclib.Placeholder('WHITESPACE', '&nbsp;', 'bla'),
        tclib.Placeholder('END_BOLD', '</b>', 'bla')]),
                                             'BINGOBONGO')
    xml = msg_node.FormatXml()
    self.failUnless(xml.find('&nbsp;') == -1, 'should have no entities')

  def testIter(self):
    # First build a little tree of message and ph nodes.
    node = message.MessageNode()
    node.StartParsing(u'message', None)
    node.HandleAttribute(u'name', u'bla')
    node.AppendContent(u" '''  two spaces  ")
    node.AppendContent(u' space before and after ')
    ph = message.PhNode()
    ph.StartParsing(u'ph', None)
    ph.AddChild(message.ExNode())
    ph.HandleAttribute(u'name', u'BINGO')
    ph.AppendContent(u'bongo')
    node.AddChild(ph)
    node.AddChild(message.PhNode())
    node.AppendContent(u" space before two after  '''")

    order = [message.MessageNode, message.PhNode, message.ExNode, message.PhNode]
    for n in node:
      self.failUnless(type(n) == order[0])
      order = order[1:]
    self.failUnless(len(order) == 0)

  def testGetChildrenOfType(self):
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
      <grit latest_public_release="2" source_lang_id="en-US"
            current_release="3" base_dir=".">
        <outputs>
          <output filename="resource.h" type="rc_header" />
          <output filename="en/generated_resources.rc" type="rc_all"
                  lang="en" />
          <if expr="pp_if('NOT_TRUE')">
            <output filename="de/generated_resources.rc" type="rc_all"
                    lang="de" />
          </if>
        </outputs>
        <release seq="3">
          <messages>
            <message name="ID_HELLO">Hello!</message>
          </messages>
        </release>
      </grit>'''
    grd = grd_reader.Parse(StringIO.StringIO(xml),
                           util.PathFromRoot('grit/test/data'))
    from grit.node import io
    output_nodes = grd.GetChildrenOfType(io.OutputNode)
    self.failUnlessEqual(len(output_nodes), 3)
    self.failUnlessEqual(output_nodes[2].attrs['filename'],
                         'de/generated_resources.rc')

if __name__ == '__main__':
  unittest.main()
