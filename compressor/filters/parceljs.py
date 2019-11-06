import os
from compressor.filters import CompilerFilter
from compressor.conf import settings
from compressor.filters.base import (
    NamedTemporaryFile, subprocess, shell_quote, FilterError, smart_text, io
)

parcel_offline_args = '--no-source-maps --no-autoinstall --no-content-hash'
parcel_args = '--no-minify --no-source-maps --no-autoinstall --no-content-hash'


class ParserFilter(CompilerFilter):
    command = "parcel build"

    def process_infile(self, options, encoding, **kwargs):
        raise NotImplementedError
    
    def process_outfile(self, options, **kwargs):
        raise NotImplementedError
    
    def process_quote(self, options, **kwargs):
        # Quote infile and outfile for spaces etc.
        if "infile" in options:
            options["infile"] = shell_quote(options["infile"])
        if "outfile" in options:
            options["outfile"] = shell_quote(options["outfile"])
    
    def execute_command(self, options, encoding, **kwargs):
        command = self.command.format(**options)
        proc = subprocess.Popen(
            command, shell=True, cwd=self.cwd, stdout=self.stdout,
            stdin=self.stdin, stderr=self.stderr)
        if self.infile is None:
            # if infile is None then send content to process' stdin
            filtered, err = proc.communicate(self.content.encode(encoding))
            return filtered, err, proc
        else:
            filtered, err = proc.communicate()
            return filtered, err, proc

    def read_output_files(self, options, encoding, **kwargs):
        outfile_path = options.get('outfile')
        if outfile_path:
            with io.open(outfile_path, 'r', encoding=encoding) as file:
                filtered = file.read()
            return filtered
    
    def close_all_file(self, options, **kwargs):
        if self.infile is not None:
            self.infile.close()
        if self.outfile is not None:
            self.outfile.close()

    def get_refined_output(self, output, **kwargs):
        return smart_text(output)

    def input(self, **kwargs):

        encoding = self.default_encoding
        options = dict(self.options)
        dirname = self.get_tmpdir()
        options["dir"] = dirname
        options['file_name'] = kwargs.get('filename')

        self.process_infile(options, encoding, **kwargs)

        self.process_outfile(options, **kwargs)

        self.process_quote(options, **kwargs)

        try:
            filtered, err, proc = self.execute_command(options, encoding, **kwargs)
            filtered, err = filtered.decode(encoding), err.decode(encoding)
        except (IOError, OSError) as e:
            raise FilterError('Unable to apply %s (%r): %s' %
                              (self.__class__.__name__, self.command, e))
        else:
            if proc.wait() != 0:
                # command failed, raise FilterError exception
                if not err:
                    err = ('Unable to apply %s (%s)' %
                           (self.__class__.__name__, self.command))
                    if filtered:
                        err += '\n%s' % filtered
                raise FilterError(err)

            if self.verbose:
                self.logger.debug(err)

            output = self.read_output_files(options, encoding, **kwargs)
        finally:
            self.close_all_file(options, **kwargs)
        return self.get_refined_output(output, **kwargs) 


class ParserFilterJS(ParserFilter):

    def input(self, **kwargs):
        _kind = kwargs.get('kind')
        if _kind == 'file':
            if (settings.COMPRESS_OFFLINE):
                self.command = self.command + " {file_name} " + parcel_offline_args + " -d {dir} --out-file {outfile}"
            else:
                self.command = self.command + " {file_name} " + parcel_args + "  -d {dir} --out-file {outfile}"
        else:
            if (settings.COMPRESS_OFFLINE):
                self.command = self.command + " {infile} " + parcel_offline_args + " -d {dir} --out-file {outfile}"
            else:
                self.command = self.command + " {infile} " + parcel_args + "  -d {dir} --out-file {outfile}"
        return super().input(**kwargs)
    
    def process_infile(self, options, encoding, **kwargs):

        if self.infile is None and "{infile}" in self.command:
            # create temporary input file if needed
            script_elem = kwargs.get('elem')
            attrs = {idx: value for idx, value in script_elem.get('attrs', None)} 
            ext = f".{attrs.get('lang')}" if attrs.get('lang') else '.js'

            if self.filename is None:
                self.infile = NamedTemporaryFile(mode='wb',dir=options['dir'], suffix=ext)
                self.infile.write(self.content.encode(encoding))
                self.infile.flush()
                options["infile"] = self.infile.name
            else:
                # we use source file directly, which may be encoded using
                # something different than utf8. If that's the case file will
                # be included with charset="something" html attribute and
                # charset will be available as filter's charset attribute
                encoding = self.charset  # or self.default_encoding
                self.infile = open(self.filename)
                options["infile"] = self.filename
    
    def process_outfile(self, options, **kwargs):
        if "{outfile}" in self.command and "outfile" not in options:
            # create temporary output file if needed
            ext = self.type and ".%s" % self.type or ""

            self.outfile = NamedTemporaryFile(mode='r+',dir=options['dir'], suffix=ext)
            options["outfile"] = self.outfile.name
            options["outfile_css"] = self.outfile.name.replace(ext, '.css')
    
    def process_quote(self, options, **kwargs):
        # Quote infile and outfile for spaces etc.
        if "infile" in options:
            options["infile"] = shell_quote(options["infile"])
        if "outfile" in options:
            options["outfile"] = shell_quote(options["outfile"])
            options["outfile_css"] = shell_quote(options["outfile_css"])

    def read_output_files(self, options, encoding, **kwargs):
        outfile_path = options.get('outfile')
        css_filtered, outfile_path_css = None, options.get('outfile_css')
        if outfile_path:
            with io.open(outfile_path, 'r', encoding=encoding) as file:
                filtered = file.read()
        if outfile_path_css and os.path.exists(outfile_path_css):
            with io.open(outfile_path_css, 'r', encoding=encoding) as file:
                css_filtered = file.read()
        return filtered, css_filtered
    
    def close_all_file(self, options, **kwargs):
        if self.infile is not None:
            self.infile.close()
        if self.outfile is not None:
            self.outfile.close()
        if os.path.exists(options.get('outfile_css')):
            os.remove(options.get('outfile_css'))
    
    def get_refined_output(self, output, **kwargs):
        filtered, css_filtered = output
        return ('js', smart_text(filtered)), ('css', smart_text(css_filtered.replace('///..', ''))) if css_filtered else ('css', css_filtered)


# django-compress has best implementation
class ParserFilterCSS(ParserFilter):

    @property
    def command(self):
        if (settings.COMPRESS_OFFLINE):
            return 'parcel build {infile} ' + parcel_offline_args + ' -d {dir} --out-file {outfile}'
        return 'parcel build {infile}  ' + parcel_args + ' -d {dir} --out-file {outfile}'

    @staticmethod
    def get_file_type(options):
        if options and options.get('attrs', None):
            attrs = options.get('attrs')
            type_ = attrs.get('type', None)
            if not type_:
                return '.css'
            values = type_.split('/')
            if len(values) > 0:
                return f".{values[1].replace('x-', '')}"
            return f".{values[0]}"
        return '.css'
    
    def process_infile(self, options, encoding, **kwargs):
        if self.infile is None and "{infile}" in self.command:
            file_type = self.get_file_type(options)
            # create temporary input file if needed
            if self.filename is None:
                self.infile = NamedTemporaryFile(mode='wb', dir=options['dir'], suffix=file_type)
                self.infile.write(self.content.encode(encoding))
                self.infile.flush()
                options["infile"] = self.infile.name
            else:
                # we use source file directly, which may be encoded using
                # something different than utf8. If that's the case file will
                # be included with charset="something" html attribute and
                # charset will be available as filter's charset attribute
                encoding = self.charset  # or self.default_encoding
                self.infile = open(self.filename)
                options["infile"] = self.filename
    
    def process_outfile(self, options, **kwargs):
        if "{outfile}" in self.command and "outfile" not in options:
            # create temporary output file if needed
            ext = self.type and ".%s" % self.type or ""
            self.outfile = NamedTemporaryFile(mode='r+', dir=options['dir'], suffix=ext)
            options["outfile"] = self.outfile.name
    
    def get_refined_output(self, output, **kwargs):
        filtered = output.replace('///..', '')
        return smart_text(filtered)

    def input(self, **kwargs):
        if not kwargs.get('method', None):
            return self.content
        
        return super().input(**kwargs)
