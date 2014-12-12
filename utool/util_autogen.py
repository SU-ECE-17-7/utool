from __future__ import absolute_import, division, print_function
from utool import util_inject
print, print_, printDBG, rrr, profile = util_inject.inject(__name__, '[alg]')


class PythonStatement(object):
    """ Thin wrapper around a string representing executable python code """
    def __init__(self, stmt):
        self.stmt = stmt
    def __repr__(self):
        return self.stmt
    def __str__(self):
        return self.stmt


def autofix_codeblock(codeblock, max_line_len=80,
                      aggressive=False,
                      very_aggressive=False,
                      experimental=False):
    r"""
    Uses autopep8 to format a block of code

    Example:
        >>> import utool
        >>> codeblock = utool.codeblock(
            '''
            def func( with , some = 'Problems' ):


             syntax ='Ok'
             but = 'Its very messy'
             if None:
                    # syntax might not be perfect due to being cut off
                    ommiting_this_line_still_works=   True
            ''')
        >>> fixed_codeblock = utool.autofix_codeblock(codeblock)
        >>> print(fixed_codeblock)
    """
    # FIXME idk how to remove the blank line following the function with
    # autopep8. It seems to not be supported by them, but it looks bad.
    import autopep8
    arglist = ['--max-line-length', '80']
    if aggressive:
        arglist.extend(['-a'])
    if very_aggressive:
        arglist.extend(['-a', '-a'])
    if experimental:
        arglist.extend(['--experimental'])
    arglist.extend([''])
    autopep8_options = autopep8.parse_args(arglist)
    fixed_codeblock = autopep8.fix_code(codeblock, options=autopep8_options)
    return fixed_codeblock


def auto_docstr(modname, funcname, verbose=True, **kwargs):
    """
    Args:
        modname (str):
        funcname (str):

    Returns:
        docstr

    Example:
        >>> import utool
        >>> utool.util_autogen.rrr(verbose=False)
        >>> #docstr = utool.auto_docstr('ibeis.model.hots.smk.smk_index', 'compute_negentropy_names')
        >>> modname = 'utool.util_autogen'
        >>> funcname = 'auto_docstr'
        >>> docstr = utool.util_autogen.auto_docstr(modname, funcname)
        >>> print(docstr)
    """
    import utool
    docstr = 'error'
    if isinstance(modname, str):
        module = __import__(modname)
        import imp
        imp.reload(module)
        #try:
        #    func = getattr(module, funcname)
        #    docstr = make_default_docstr(func)
        #    return docstr
        #except Exception as ex1:
        #docstr = 'error ' + str(ex1)
        #if utool.VERBOSE:
        #    print('make_default_docstr is falling back')
        #print(ex)
        #print('modname = '  + modname)
        #print('funcname = ' + funcname)
        try:
            # FIXME: PYTHON 3
            execstr = utool.codeblock(
                '''
                import {modname}
                import imp
                imp.reload({modname})
                import utool
                imp.reload(utool.util_autogen)
                imp.reload(utool.util_inspect)
                func = {modname}.{funcname}
                docstr = utool.util_autogen.make_default_docstr(func, **kwargs)
                '''
            ).format(**locals())
            exec(execstr)
            #return 'BARFOOO' +  docstr
            return docstr
            #print(execstr)
        except Exception as ex2:
            docstr = 'error ' + str(ex2)
            if verbose:
                import utool
                #utool.printex(ex1, 'ex1')
                utool.printex(ex2, 'ex2', tb=True)
            error_str = utool.formatex(ex2, 'ex2', tb=True, keys=['modname', 'funcname'])
            return error_str
            #return docstr + '\n' + execstr
    else:
        docstr = 'error'
    return docstr


def print_auto_docstr(modname, funcname):
    """
    python -c "import utool; utool.print_auto_docstr('ibeis.model.hots.smk.smk_index', 'compute_negentropy_names')"
    python -c "import utool;
    utool.print_auto_docstr('ibeis.model.hots.smk.smk_index', 'compute_negentropy_names')"
    """
    print(auto_docstr(modname, funcname))


# <INVIDIAL DOCSTR COMPONENTS>

def make_args_docstr(argname_list, argtype_list, argdesc_list, ismethod):
    r"""
    make_args_docstr

    Args:
        argname_list (list): names
        argtype_list (list): types
        argdesc_list (list): descriptions

    Returns:
        str: arg_docstr

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_autogen import *  # NOQA
        >>> argname_list = ['argname_list', 'argtype_list', 'argdesc_list']
        >>> argtype_list = ['list', 'list', 'list']
        >>> argdesc_list = ['names', 'types', 'descriptions']
        >>> ismethod = False
        >>> arg_docstr = make_args_docstr(argname_list, argtype_list, argdesc_list, ismethod)
        >>> result = str(arg_docstr)
        >>> print(result)
        argname_list (list): names
        argtype_list (list): types
        argdesc_list (list): descriptions

    """
    import utool as ut
    if ismethod:
        argname_list = argname_list[1:]
        argtype_list = argtype_list[1:]
        argdesc_list = argdesc_list[1:]
    argdoc_list = [arg + ' (%s): %s' % (_type, desc)
                   for arg, _type, desc in zip(argname_list, argtype_list, argdesc_list)]
    # align?
    align_args = False
    if align_args:
        argdoc_aligned_list = ut.align_lines(argdoc_list, character='(')
        arg_docstr = '\n'.join(argdoc_aligned_list)
    else:
        arg_docstr = '\n'.join(argdoc_list)
    return arg_docstr


def make_returns_or_yeilds_docstr(return_type, return_name, return_desc):
    return_doctr = return_type + ': '
    if return_name is not None:
        return_doctr += return_name
        if len(return_desc) > 0:
            return_doctr += ' - '
    return_doctr += return_desc
    return return_doctr


def make_example_docstr(funcname=None, modname=None, argname_list=None,
                        defaults=None, return_type=None, return_name=None,
                        ismethod=False):
    """
    Creates skeleton code to build an example doctest
    """
    import utool as ut
    examplecode_lines = []
    top_import_fmstr = 'from {modname} import *  # NOQA'
    top_import = top_import_fmstr.format(modname=modname)
    import_lines = [top_import]

    # TODO: Externally register these
    default_argval_map = {
        'ibs':      'ibeis.opendb(\'testdb1\')',
        'aid_list': 'ibs.get_valid_aids()',
        'nid_list': 'ibs._get_all_known_nids()',
    }
    import_depends_map = {
        'ibs':      'import ibeis',
    }

    def find_arg_defaultval(argname, val):
        if val == '?':
            if argname in default_argval_map:
                val = ut.PythonStatement(default_argval_map[argname])
                if argname in import_depends_map:
                    import_lines.append(import_depends_map[argname])
        return val

    # Default example values
    defaults_ = [] if defaults is None else defaults
    num_unknown = (len(argname_list) - len(defaults_))
    default_vals = ['?'] * num_unknown + list(defaults_)
    arg_val_iter = zip(argname_list, default_vals)
    infered_defaults = [find_arg_defaultval(argname, val)
                        for argname, val in arg_val_iter]
    arg_inferval_iter = zip(argname_list, infered_defaults)
    argdef_lines = ['%s = %r' % (argname, inferval)
                    for argname, inferval in arg_inferval_iter]
    import_lines = ut.unique_ordered(import_lines)

    if any([inferval == '?' for inferval in infered_defaults]):
        examplecode_lines.append('# DISABLE_DOCTEST')
    else:
        # Enable the test if it can be run immediately
        examplecode_lines.append('# ENABLE_DOCTEST')

    examplecode_lines.extend(import_lines)
    examplecode_lines.extend(argdef_lines)
    # Default example result assignment
    result_assign = ''
    result_print = None
    if 'return_name' in vars():
        if return_type is not None:
            if return_name is None:
                return_name = 'result'
            result_assign = return_name + ' = '
            result_print = 'print(result)'  # + return_name + ')'
    # Default example call
    if ismethod:
        selfname = argname_list[0]
        methodargs = ', '.join(argname_list[1:])
        tup = (selfname, '.', funcname, '(', methodargs, ')')
        example_call = ''.join(tup)
    else:
        funcargs = ', '.join(argname_list)
        tup = (funcname, '(', funcargs, ')')
        example_call = ''.join(tup)
    examplecode_lines.append(result_assign + example_call)
    if result_print is not None:
        if return_name != 'result':
            examplecode_lines.append('result = str(' + return_name + ')')
        examplecode_lines.append(result_print)
    examplecode = '\n'.join(examplecode_lines)
    return examplecode


def make_cmdline_docstr(funcname, modname):
    cmdline_fmtstr = 'python -m {modname} --test-{funcname}'  # --enableall'
    return cmdline_fmtstr.format(**locals())

# </INVIDIAL DOCSTR COMPONENTS>


def make_docstr_block(header, block):
    import utool as ut
    indented_block = '\n' + ut.indent(block)
    docstr_block = ''.join([header, ':', indented_block])
    return docstr_block


def make_default_docstr(func,
                        with_args=True,
                        with_ret=True,
                        with_commandline=True,
                        with_example=True,
                        with_header=False,
                        with_debug=False,
                        ):
    r"""
    Tries to make a sensible default docstr so the user
    can fill things in without typing too much

    # TODO: Interleave old documentation with new documentation

    Args:
        func (function): live python function

    Returns:
        tuple: (argname, val)

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_autogen import *  # NOQA
        >>> import utool as ut
        >>> func = ut.make_default_docstr
        >>> func = ut.make_args_docstr
        >>> default_docstr = make_default_docstr(func)
        >>> result = str(default_docstr)
        >>> print(result)

    """
    import utool as ut
    funcinfo = ut.infer_function_info(func)

    argname_list   = funcinfo.argname_list
    argtype_list   = funcinfo.argtype_list
    argdesc_list   = funcinfo.argdesc_list
    return_header  = funcinfo.return_header
    return_type    = funcinfo.return_type
    return_name    = funcinfo.return_name
    return_desc    = funcinfo.return_desc
    funcname       = funcinfo.funcname
    modname        = funcinfo.modname
    defaults       = funcinfo.defaults
    num_indent     = funcinfo.num_indent
    needs_surround = funcinfo.needs_surround
    funcname       = funcinfo.funcname
    ismethod       = funcinfo.ismethod

    docstr_parts = []

    # Header part
    if with_header:
        header_block = funcname
        docstr_parts.append(header_block)

    # Args part
    if with_args and len(argname_list) > 0:
        argheader = 'Args'
        arg_docstr = make_args_docstr(argname_list, argtype_list, argdesc_list, ismethod)
        argsblock = make_docstr_block(argheader, arg_docstr)
        docstr_parts.append(argsblock)

    # Return / Yeild part
    if with_ret and return_header is not None:
        if return_header is not None:
            return_doctr = make_returns_or_yeilds_docstr(return_type, return_name, return_desc)
            returnblock = make_docstr_block(return_header, return_doctr)
            docstr_parts.append(returnblock)

    # Example part
    # try to generate a simple and unit testable example
    if with_commandline:
        cmdlineheader = 'CommandLine'
        cmdlinecode = make_cmdline_docstr(funcname, modname)
        cmdlineblock = make_docstr_block(cmdlineheader, cmdlinecode)
        docstr_parts.append(cmdlineblock)

    if with_example:
        exampleheader = 'Example'
        examplecode = make_example_docstr(funcname, modname, argname_list,
                                          defaults, return_type, return_name,
                                          ismethod)
        examplecode_ = ut.indent(examplecode, '>>> ')
        exampleblock = make_docstr_block(exampleheader, examplecode_)
        docstr_parts.append(exampleblock)

    # DEBUG part (in case something goes wrong)
    if with_debug:
        debugheader = 'Debug'
        debugblock = ut.codeblock(
            '''
            num_indent = {num_indent}
            '''
        ).format(num_indent=num_indent)
        debugblock = make_docstr_block(debugheader, debugblock)
        docstr_parts.append(debugblock)

    # Enclosure / Indentation Parts
    if needs_surround:
        docstr_parts = ['r"""'] + ['\n\n'.join(docstr_parts)] + ['"""']
        default_docstr = '\n'.join(docstr_parts)
    else:
        default_docstr = '\n\n'.join(docstr_parts)

    docstr_indent = ' ' * (num_indent + 4)
    default_docstr = ut.indent(default_docstr, docstr_indent)
    return default_docstr


def make_default_module_maintest(modname):
    """
    make_default_module_maintest

    Args:
        modname (str):  module name

    Returns:
        str: text

    References:
        http://legacy.python.org/dev/peps/pep-0338/

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_autogen import *  # NOQA
        >>> modname = 'utool.util_autogen'
        >>> text = make_default_module_maintest(modname)
        >>> result = str(text)
        >>> print(result)
    """
    import utool as ut
    # Need to use python -m to run a module
    # otherwise their could be odd platform specific errors.
    #python -c "import utool, {modname};
    # utool.doctest_funcs({modname}, allexamples=True)"
    text = ut.codeblock(
        '''
        if __name__ == '__main__':
            """
            CommandLine:
                python -m {modname}
                python -m {modname} --allexamples
                python -m {modname} --allexamples --noface --nosrc
            """
            import multiprocessing
            multiprocessing.freeze_support()  # for win32
            import utool as ut  # NOQA
            ut.doctest_funcs()
        '''
    ).format(modname=modname)
    return text


if __name__ == '__main__':
    """
    CommandLine:
        python ibeis/control/template_generator.py --tbls annotations --Tflags getters native
        python -c "import utool, utool.util_autogen; utool.doctest_funcs(utool.util_autogen, allexamples=True)"
        python -m utool.util_autogen
        python -m utool.util_autogen --allexamples
        python -m utool.util_autogen --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()