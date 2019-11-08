import os
import six
from django import template
from compressor.conf import settings
from django.utils.safestring import mark_safe
from compressor.finders import PrivateFileSystemFinder

private_file_finder = PrivateFileSystemFinder()
register = template.Library()
PRIVATE_STATIC = "/private_static/"

@register.simple_tag
def private_static(basename):
    filepath = get_private_static_fullpath(basename)
    if filepath:
        filepath = f"{PRIVATE_STATIC}{basename}"
        return mark_safe(filepath)
    raise FileExistsError(f'{basename} not found in COMPRESS_PRIVATE_DIRS')


def get_basename_from_private_static(basename):
    full_file = get_private_static_fullpath(basename)
    base_name = full_file.split('/')
    return '/'.join([base_name[len(base_name)-2], base_name[len(base_name)-1]]), full_file


def path_exist(filename):
    return os.path.exists(filename)

def is_private_static_path(filename):
    return PRIVATE_STATIC in filename

def get_private_static_fullpath(basename):
    basename = basename.replace(PRIVATE_STATIC, '')
    return private_file_finder.find(basename)