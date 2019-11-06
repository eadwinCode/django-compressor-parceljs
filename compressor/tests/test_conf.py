from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured
from compressor.conf import settings
from compressor.conf import CompressorConf


default_css_filters = ['compressor.filters.css_default.CssAbsoluteFilter']
default_js_filters = ['compressor.filters.jsmin.JSMinFilter']
default_parcel_filters = ['compressor.filters.parceljs.ParserFilterJS']


def create_conf(**attrs):
    # Creating a new appconf.AppConf subclass will cause
    # its configuration to be resolved.
    # We use this to force the CompressorConf to be re-resolved,
    # when we've changed the settings.
    attrs['__module__'] = None
    return type(
        'TestCompressorConf',
        (CompressorConf, ),
        attrs)


class ConfTestCase(SimpleTestCase):
    def test_filter_defaults(self):
        # This used the settings from compressor/test_settings.py
        # which contains no values for filers and therefore uses the defaults.
        self.assertEqual(settings.COMPRESS_FILTERS['css'], default_css_filters)
        self.assertEqual(settings.COMPRESS_FILTERS['js'], default_js_filters)
        self.assertEqual(settings.COMPRESS_FILTERS['parcel'], default_parcel_filters)
        self.assertFalse(hasattr(settings, 'COMPRESS_CSS_FILTERS'))
        self.assertFalse(hasattr(settings, 'COMPRESS_JS_FILTERS'))
        self.assertFalse(hasattr(settings, 'COMPRESS_PARCEL_FILTERS'))

    @override_settings(COMPRESS_FILTERS=dict(),
                       COMPRESS_CSS_FILTERS=None,
                       COMPRESS_PARCEL_FILTERS=None,
                       COMPRESS_JS_FILTERS=None)
    def test_filters_by_default(self):
        conf = create_conf()
        self.assertEqual(conf.FILTERS['css'], default_css_filters)
        self.assertEqual(conf.FILTERS['js'], default_js_filters)
        self.assertEqual(conf.FILTERS['parcel'], default_parcel_filters)
        self.assertFalse(hasattr(conf, 'COMPRESS_CSS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_JS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_PARCEL_FILTERS'))

    @override_settings(COMPRESS_FILTERS=dict(),
                       COMPRESS_CSS_FILTERS=['ham'],
                       COMPRESS_JS_FILTERS=['spam'],
                       COMPRESS_PARCEL_FILTERS=['parceljs'],
                       )
    def test_filters_by_specific_settings(self):
        conf = create_conf()
        self.assertEqual(conf.FILTERS['css'], ['ham'])
        self.assertEqual(conf.FILTERS['js'], ['spam'])
        self.assertEqual(conf.FILTERS['parcel'], ['parceljs'])
        self.assertFalse(hasattr(conf, 'COMPRESS_CSS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_JS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_PARCEL_FILTERS'))

    @override_settings(COMPRESS_FILTERS=dict(css=['ham'], js=['spam'], parcel=['parceljs']),
                       COMPRESS_CSS_FILTERS=None,
                       COMPRESS_JS_FILTERS=None)
    def test_filters_by_main_setting(self):
        conf = create_conf()
        self.assertEqual(conf.FILTERS['css'], ['ham'])
        self.assertEqual(conf.FILTERS['js'], ['spam'])
        self.assertEqual(conf.FILTERS['parcel'], ['parceljs'])
        self.assertFalse(hasattr(conf, 'COMPRESS_CSS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_JS_FILTERS'))
        self.assertFalse(hasattr(conf, 'COMPRESS_PARCEL_FILTERS'))

    @override_settings(COMPRESS_FILTERS=dict(css=['ham']),
                       COMPRESS_CSS_FILTERS=['spam'])
    def test_css_filters_conflict(self):
        with self.assertRaises(ImproperlyConfigured):
            create_conf()

    @override_settings(COMPRESS_FILTERS=dict(js=['ham']),
                       COMPRESS_JS_FILTERS=['spam'])
    def test_js_filters_conflict(self):
        with self.assertRaises(ImproperlyConfigured):
            create_conf()

    @override_settings(COMPRESS_FILTERS=dict(parcel=['parceljs']),
                       COMPRESS_PARCEL_FILTERS=['spam'])
    def test_js_filters_conflict(self):
        with self.assertRaises(ImproperlyConfigured):
            create_conf()
