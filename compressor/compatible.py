try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_str
    smart_text = smart_str

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_str
    force_text = force_str
