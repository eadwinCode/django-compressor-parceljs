import os
import six
from django import template
from compressor.conf import settings
from django.utils.safestring import mark_safe
from compressor.finders import PrivateFileSystemFinder

private_file_finder = PrivateFileSystemFinder()
register = template.Library()


@register.simple_tag
def private_static(basename):
    filepath = private_file_finder.find(basename)
    if filepath:
        return mark_safe(filepath)
    raise FileExistsError(f'{basename} not found in COMPRESS_PRIVATE_DIRS')
