from compressor.utils import staticfiles
from compressor.storage import CompressorFileStorage
import os
from django.conf import settings
from django.core.files.storage import (
    FileSystemStorage,
)
from collections import OrderedDict
from django.core.checks import Error
from django.utils._os import safe_join
from django.contrib.staticfiles import utils


class CompressorFinder(staticfiles.finders.BaseStorageFinder):
    """
    A staticfiles finder that looks in COMPRESS_ROOT
    for compressed files, to be used during development
    with staticfiles development file server or during
    deployment.
    """
    storage = CompressorFileStorage

    def list(self, ignore_patterns):
        return []


searched_locations = []


class PrivateFileSystemFinder(staticfiles.finders.BaseFinder):
    """
    A static files finder that uses the ``COMPRESS_PRIVATE_DIRS`` setting
    to locate files.
    """
    def __init__(self, app_names=None, *args, **kwargs):
        # List of locations with static files
        self.locations = []
        # Maps dir paths to an appropriate storage instance
        self.storages = OrderedDict()
        for root in settings.COMPRESS_PRIVATE_DIRS:
            if isinstance(root, (list, tuple)):
                prefix, root = root
            else:
                prefix = ''
            if (prefix, root) not in self.locations:
                self.locations.append((prefix, root))
        for prefix, root in self.locations:
            filesystem_storage = FileSystemStorage(location=root)
            filesystem_storage.prefix = prefix
            self.storages[root] = filesystem_storage
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = []
        if not isinstance(settings.COMPRESS_PRIVATE_DIRS, (list, tuple)):
            errors.append(Error(
                'The COMPRESS_PRIVATE_DIRS setting is not a tuple or list.',
                hint='Perhaps you forgot a trailing comma?',
                id='staticfiles.E001',
            ))
        for root in settings.COMPRESS_PRIVATE_DIRS:
            if isinstance(root, (list, tuple)):
                prefix, root = root
                if prefix.endswith('/'):
                    errors.append(Error(
                        'The prefix %r in the COMPRESS_PRIVATE_DIRS setting must '
                        'not end with a slash.' % prefix,
                        id='staticfiles.E003',
                    ))
            if settings.STATIC_ROOT and os.path.abspath(settings.STATIC_ROOT) == os.path.abspath(root):
                errors.append(Error(
                    'The COMPRESS_PRIVATE_DIRS setting should not contain the '
                    'STATIC_ROOT setting.',
                    id='staticfiles.E002',
                ))
        return errors

    def find(self, path, all=False):
        """
        Look for files in the extra locations as defined in PRIVATE_DIRS.
        """
        matches = []
        for prefix, root in self.locations:
            if root not in searched_locations:
                searched_locations.append(root)
            matched_path = self.find_location(root, path, prefix)
            if matched_path:
                if not all:
                    return matched_path
                matches.append(matched_path)
        return matches

    def find_location(self, root, path, prefix=None):
        """
        Find a requested static file in a location and return the found
        absolute path (or ``None`` if no match).
        """
        if prefix:
            prefix = '%s%s' % (prefix, os.sep)
            if not path.startswith(prefix):
                return None
            path = path[len(prefix):]
        path = safe_join(root, path)
        if os.path.exists(path):
            return path

    def list(self, ignore_patterns):
        """
        List all files in all locations.
        """
        for prefix, root in self.locations:
            storage = self.storages[root]
            for path in utils.get_files(storage, ignore_patterns):
                yield path, storage
