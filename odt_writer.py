"""
ODT Document Writer Module
==========================

This module creates OpenDocument Text (ODT) files for saved news articles.
ODT is an open standard format that can be opened with LibreOffice Writer, 
Microsoft Word, and other word processors.
"""

import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_odt_document(article_data, filepath):
    """
    Create an ODT document for a news article.
    
    Args:
        article_data (dict): Article information
        filepath (str): Path where to save the ODT file
    """
    
    # ODT manifest content
    manifest_content = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''

    # ODT meta content
    meta_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.2">
  <office:meta>
    <meta:generator>Telegram News Agent</meta:generator>
    <dc:title>{escape_xml(article_data.get('title', 'News Article'))}</dc:title>
    <dc:creator>{escape_xml(article_data.get('author', 'Unknown'))}</dc:creator>
    <meta:creation-date>{article_data.get('date_extracted', '')}T{article_data.get('time_extracted', '')}:00</meta:creation-date>
    <dc:date>{article_data.get('date_extracted', '')}T{article_data.get('time_extracted', '')}:00</dc:date>
  </office:meta>
</office:document-meta>'''

    # ODT styles content
    styles_content = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2">
  <office:styles>
    <style:default-style style:family="paragraph">
      <style:paragraph-properties style:tab-stop-distance="1.27cm"/>
      <style:text-properties fo:font-family="Arial" style:font-family-generic="swiss" style:font-pitch="variable" fo:font-size="12pt"/>
    </style:default-style>
    <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
    <style:style style:name="Title" style:family="paragraph" style:class="title">
      <style:paragraph-properties fo:text-align="center"/>
      <style:text-properties fo:font-size="18pt" fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Subtitle" style:family="paragraph" style:class="subtitle">
      <style:paragraph-properties fo:text-align="center"/>
      <style:text-properties fo:font-size="14pt" fo:font-style="italic"/>
    </style:style>
    <style:style style:name="Heading_20_1" style:display-name="Heading 1" style:family="paragraph" style:class="text">
      <style:text-properties fo:font-size="16pt" fo:font-weight="bold"/>
    </style:style>
  </office:styles>
</office:document-styles>'''

    # Create main content
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" office:version="1.2">
  <office:body>
    <office:text>
      <text:p text:style-name="Title">{escape_xml(article_data.get('title', 'News Article'))}</text:p>
      <text:p text:style-name="Subtitle">Extracted from Telegram News Agent</text:p>
      <text:p text:style-name="Standard"/>
      
      <text:p text:style-name="Heading_20_1">Article Information</text:p>
      <text:p text:style-name="Standard"><text:span text:style-name="Bold">Author:</text:span> {escape_xml(article_data.get('author', 'Unknown'))}</text:p>
      <text:p text:style-name="Standard"><text:span text:style-name="Bold">Date Extracted:</text:span> {article_data.get('date_extracted', 'Unknown')} at {article_data.get('time_extracted', 'Unknown')}</text:p>
      <text:p text:style-name="Standard"><text:span text:style-name="Bold">Source URL:</text:span> {escape_xml(article_data.get('url', ''))}</text:p>
      {get_llm_info_content(article_data)}
      <text:p text:style-name="Standard"/>
      
      <text:p text:style-name="Heading_20_1">Summary</text:p>
      <text:p text:style-name="Standard">{escape_xml(article_data.get('summary', 'No summary available'))}</text:p>
      <text:p text:style-name="Standard"/>
      
      {get_key_points_content(article_data)}
      
      <text:p text:style-name="Heading_20_1">Image</text:p>
      <text:p text:style-name="Standard">{escape_xml(article_data.get('image', 'No image available'))}</text:p>
    </office:text>
  </office:body>
</office:document-content>'''

    # Create ODT file (it's actually a ZIP file)
    try:
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as odt_file:
            # Add mimetype file (must be first and uncompressed)
            odt_file.writestr('mimetype', 'application/vnd.oasis.opendocument.text', zipfile.ZIP_STORED)
            
            # Add META-INF directory and manifest
            odt_file.writestr('META-INF/manifest.xml', manifest_content)
            
            # Add main content files
            odt_file.writestr('content.xml', content)
            odt_file.writestr('styles.xml', styles_content)
            odt_file.writestr('meta.xml', meta_content)
            
    except Exception as e:
        raise Exception(f"Error creating ODT file: {e}")

def get_llm_info_content(article_data):
    """Generate LLM information content for ODT"""
    if not article_data.get('enhanced_by_llm', False):
        return '<text:p text:style-name="Standard"><text:span text:style-name="Bold">Processing:</text:span> Basic extraction only</text:p>'
    
    content = f'<text:p text:style-name="Standard"><text:span text:style-name="Bold">Enhanced by:</text:span> {escape_xml(article_data.get("llm_provider", "LLM").upper())}</text:p>'
    
    if article_data.get('category'):
        content += f'<text:p text:style-name="Standard"><text:span text:style-name="Bold">Category:</text:span> {escape_xml(article_data.get("category"))}</text:p>'
    
    if article_data.get('article_type'):
        content += f'<text:p text:style-name="Standard"><text:span text:style-name="Bold">Type:</text:span> {escape_xml(article_data.get("article_type"))}</text:p>'
    
    if article_data.get('confidence'):
        content += f'<text:p text:style-name="Standard"><text:span text:style-name="Bold">Confidence:</text:span> {escape_xml(article_data.get("confidence"))}</text:p>'
    
    return content

def get_key_points_content(article_data):
    """Generate key points content for ODT"""
    if not article_data.get('key_points'):
        return ""
    
    content = '<text:p text:style-name="Heading_20_1">Key Points</text:p>'
    for point in article_data.get('key_points', []):
        content += f'<text:p text:style-name="Standard">• {escape_xml(point)}</text:p>'
    content += '<text:p text:style-name="Standard"/>'
    
    return content

def escape_xml(text):
    """Escape special XML characters in text"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Replace XML special characters
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    
    return text