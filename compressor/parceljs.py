from compressor.conf import settings
from compressor.js import JsCompressor
from compressor.base import (render_to_string, os,
    CompressorError, mark_safe, post_compress, ContentFile, get_hexdigest
)


class ParcelJsCompressor(JsCompressor):
    output_mimetypes = {'text/javascript', 'text/css'}

    def handle_parcel_filepath(self, content, resource_kind, basename=None):
        """
        Returns file path for an output file based on contents.
        Returned path is relative to compressor storage's base url, for
        example "CACHE/css/58a8c0714e59.css".
        When `basename` argument is provided then file name (without extension)
        will be used as a part of returned file name, for example:
        get_filepath(content, "my_file.css") -> 'CACHE/css/my_file.58a8c0714e59.css'
        """
        parts = []
        if basename:
            filename = os.path.split(basename)[1]
            parts.append(os.path.splitext(filename)[0])
        parts.extend([get_hexdigest(content, 12), resource_kind])
        return os.path.join(self.output_dir, resource_kind, '.'.join(parts))

    def filter(self, content, filters, method, **kwargs):
        for filter_cls in filters:
            filter_func = getattr(
                filter_cls(content, filter_type=self.resource_kind), method)
            try:
                if callable(filter_func):
                    content = filter_func(**kwargs)
                    if isinstance(content, tuple):
                        break
            except NotImplementedError:
                pass
        return content

    def filter_input(self, forced=False):
        """
        Passes each hunk (file or code) to the 'input' methods
        of the compressor filters.
        """
        content = {'js': None, 'css': None}
        for hunk in self.hunks(forced=True):
            for key, value in hunk:
                content[key] = f"{content[key]}; {value}" if content[key] else value
        return list(content.items()) 

    def output(self, *args, **kwargs):
        if (settings.COMPRESS_ENABLED or settings.COMPRESS_PRECOMPILERS or
                kwargs.get('forced', False)):
            self.split_contents()
            if hasattr(self, 'extra_nodes'):
                return super().output(*args, **kwargs)
        return self.compress_output(*args, **kwargs)

    def compress_output(self, mode='file', forced=False, basename=None):
        """
        The general output method, override in subclass if you need to do
        any custom modification. Calls other mode specific methods or simply
        returns the content directly.
        """
        output = self.filter_input(forced)

        if not output:
            return ''

        return self.handle_output(mode, output, forced, basename)

    def handle_output(self, mode, content, forced, basename=None):
        # Then check for the appropriate output method and call it
        output_func = getattr(self, "output_%s" % mode, None)
        if callable(output_func):
            return output_func(mode, content, forced, basename)
        # Total failure, raise a general exception
        raise CompressorError(
            "Couldn't find output method for mode '%s'" % mode)

    def output_file(self, mode, content, forced=False, basename=None):
        """
        The output method that saves the content to a file and renders
        the appropriate template with the file's URL.
        """
        content_url = {}

        for key, value in content:
            if value:
                new_filepath = self.handle_parcel_filepath(value, key, basename=basename)
                if not self.storage.exists(new_filepath) or forced:
                    self.storage.save(new_filepath, ContentFile(value.encode(self.charset)))
                content_url.update({ key: mark_safe(self.storage.url(new_filepath)) })
        return self.render_output(mode, content_url)

    def output_inline(self, mode, content, forced=False, basename=None):
        """
        The output method that directly returns the content for inline
        display.
        """
        return self.render_output(mode, {"content": content})

    def output_preload(self, mode, content, forced=False, basename=None):
        """
        The output method that returns <link> with rel="preload" and
        proper href attribute for given file.
        """
        return self.output_file(mode, content, forced, basename)

    def render_output(self, mode, context=None):
        """
        Renders the compressor output with the appropriate template for
        the given mode and template context.
        """
        # Just in case someone renders the compressor outside
        # the usual template rendering cycle
        if 'compressed' not in self.context:
            self.context['compressed'] = {}
        if context:
            self.context['compressed'].update(context)
        self.context['compressed'].update(self.extra_context)

        if hasattr(self.context, 'flatten'):
            # Passing Contexts to Template.render is deprecated since Django 1.8.
            final_context = self.context.flatten()
        else:
            final_context = self.context

        post_compress.send(sender=self.__class__, type=self.resource_kind,
                           mode=mode, context=final_context)
        template_name = self.get_template_name(mode)
        return render_to_string(template_name, context=final_context)

