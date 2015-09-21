"""
python -c "import utool, doctest; print(doctest.testmod(utool.util_path))"

This module becomes nav
"""

from __future__ import absolute_import, division, print_function
from six.moves import zip, filter, filterfalse, map, range
import six
from os.path import (join, basename, relpath, normpath, split, isdir, isfile,
                     exists, islink, ismount, dirname, splitext, realpath,
                     splitdrive)
import os
import re
import sys
import shutil
import fnmatch
import warnings
from utool.util_regex import extend_regex
from utool import util_dbg
from utool.util_progress import progress_func
from utool._internal import meta_util_path
from utool import util_inject
from utool import util_arg
from utool._internal.meta_util_arg import NO_ASSERTS, VERBOSE, VERYVERBOSE, QUIET
print, print_, printDBG, rrr, profile = util_inject.inject(__name__, '[util_path]')


PRINT_CALLER = util_arg.get_argflag('--print-caller')  # FIXME: name

__IMG_EXTS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.ppm']
__LOWER_EXTS = list(ext.lower() for ext in __IMG_EXTS)
__UPPER_EXTS = list(ext.upper() for ext in __IMG_EXTS)
IMG_EXTENSIONS =  set(__LOWER_EXTS + __UPPER_EXTS)


def newcd(path):
    """ DEPRICATE """
    cwd = os.getcwd()
    os.chdir(path)
    return cwd


unixpath = meta_util_path.unixpath
truepath = meta_util_path.truepath
unixjoin = meta_util_path.unixjoin


def relpath_unix(path, otherpath):
    return relpath(path, otherpath).replace('\\', '/')


def truepath_relative(path, otherpath=None):
    """ Normalizes and returns absolute path with so specs  """
    if otherpath is None:
        otherpath = truepath(os.getcwd())
    return normpath(relpath(path, otherpath))


def tail(fpath, n=2):
    """ Alias for path_ndir_split """
    return path_ndir_split(fpath, n=n)


def path_ndir_split(path_, n, force_unix=True, winroot='C:'):
    r"""
    Shows only a little bit of the path. Up to the n bottom-level directories

    TODO: rename to path_tail? ndir_split?

    Returns:
        (str) the trailing n paths of path.

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> paths = [r'/usr/bin/local/foo/bar',
        ...          r'C:/',
        ...          #r'lonerel',
        ...          #r'reldir/other',
        ...          #r'/ham',
        ...          #r'/spam/eggs',
        ...          r'C:\Program Files (x86)/foobar/bin',]
        >>> N = 2
        >>> iter_ = ut.iprod(paths, range(1, N + 1))
        >>> force_unix = True
        >>> tuplist = [(n, path_ndir_split(path_, n)) for path_, n in iter_]
        >>> chunklist = list(ut.ichunks(tuplist, N))
        >>> list_ = [['n=%r: %r' % tup for tup in chunk] for chunk in chunklist]
        >>> line_list = [', '.join(strs) for strs in list_]
        >>> result = '\n'.join(line_list)
        >>> print(result)
        n=1: 'bar', n=2: 'foo/bar'
        n=1: 'C:/', n=2: 'C:/'
        n=1: 'bin', n=2: 'foobar/bin'
    """
    if n is None:
        return ensure_crossplat_path(path_)
    if n == 0:
        return ''
    sep = '/' if force_unix else os.sep
    ndirs_list = []
    head = path_
    for nx in range(n):
        head, tail = split(head)
        if tail == '':
            if head == '':
                break
            else:
                root = head if len(ndirs_list) == 0 else head.strip('\\/')
                ndirs_list.append(root)
                break
        else:
            ndirs_list.append(tail)
    ndirs = sep.join(ndirs_list[::-1])
    cplat_path = ensure_crossplat_path(ndirs)
    return cplat_path


def remove_file(fpath, verbose=True, dryrun=False, ignore_errors=True, **kwargs):
    """ Removes a file """
    if dryrun:
        if verbose:
            print('[util_path] Dryrem %r' % fpath)
        return
    else:
        try:
            os.remove(fpath)
            if verbose and not QUIET:
                print('[util_path] Removed %r' % fpath)
        except OSError:
            print('[util_path.remove_file] Misrem %r' % fpath)
            #warnings.warn('OSError: %s,\n Could not delete %s' % (str(e), fpath))
            if not ignore_errors:
                raise
            return False
    return True


def remove_dirs(dpath, dryrun=False, ignore_errors=True, quiet=QUIET, **kwargs):
    """ Removes a directory """
    if not quiet:
        print('[util_path] Removing directory: %r' % dpath)
    try:
        shutil.rmtree(dpath)
    except OSError as e:
        warnings.warn('OSError: %s,\n Could not delete %s' % (str(e), dpath))
        if not ignore_errors:
            raise
        return False
    return True

#import os


def augpath(path, augsuf='', augext='', augdir=None, newext=None, newfname=None, ensure=False):
    """
    augments end of path before the extension.

    augpath

    Args:
        path (str):
        augsuf (str): augment filename before extension

    Returns:
        str: newpath

    Example:
        >>> from utool.util_path import *  # NOQA
        >>> path = 'somefile.txt'
        >>> augsuf = '_aug'
        >>> newpath = augpath(path, augsuf)
        >>> result = str(newpath)
        >>> print(result)
        somefile_aug.txt

    Example:
        >>> from utool.util_path import *  # NOQA
        >>> path = 'somefile.txt'
        >>> augsuf = '_aug2'
        >>> newext = '.bak'
        >>> augdir = 'backup'
        >>> newpath = augpath(path, augsuf, newext=newext, augdir=augdir)
        >>> result = str(newpath)
        >>> print(result)
        backup/somefile_aug2.bak
    """
    # Breakup path
    dpath, fname = split(path)
    fname_noext, ext = splitext(fname)
    if newfname is not None:
        fname_noext = newfname
    # Augment ext
    if newext is None:
        newext = ext
    # Augment fname
    new_fname = ''.join((fname_noext, augsuf, newext, augext))
    # Augment dpath
    if augdir is not None:
        new_dpath = join(dpath, augdir)
        if ensure:
            # create new dir if needebe
            ensuredir(new_dpath)
    else:
        new_dpath = dpath
    # Recombine into new path
    newpath = join(new_dpath, new_fname)
    return newpath


def touch(fname, times=None, verbose=True):
    """
    Args:
        fname (str)
        times (None):
        verbose (bool):

    Example:
        >>> from utool.util_path import *  # NOQA
        >>> fname = '?'
        >>> times = None
        >>> verbose = True
        >>> result = touch(fname, times, verbose)
        >>> print(result)

    References:
        'http://stackoverflow.com/questions/1158076/implement-touch-using-python'
    """
    try:
        if verbose:
            print('[util_path] touching %r' % fname)
        with open(fname, 'a'):
            os.utime(fname, times)
    except Exception as ex:
        import utool
        utool.printex(ex, 'touch %s' % fname)
        raise


def remove_files_in_dir(dpath, fname_pattern_list='*', recursive=False, verbose=VERBOSE,
                        dryrun=False, ignore_errors=False, **kwargs):
    """ Removes files matching a pattern from a directory """
    if isinstance(fname_pattern_list, six.string_types):
        fname_pattern_list = [fname_pattern_list]
    if not QUIET:
        print('[util_path] Removing files:')
        print('  * from dpath = %r ' % dpath)
        print('  * with patterns = %r' % fname_pattern_list)
        print('  * recursive = %r' % recursive)
    num_removed, num_matched = (0, 0)
    kwargs.update({
        'dryrun': dryrun,
        'verbose': verbose,
    })
    if not exists(dpath):
        msg = ('!!! dir = %r does not exist!' % dpath)
        if not QUIET:
            print(msg)
        warnings.warn(msg, category=UserWarning)
    for root, dname_list, fname_list in os.walk(dpath):
        for fname_pattern in fname_pattern_list:
            for fname in fnmatch.filter(fname_list, fname_pattern):
                num_matched += 1
                num_removed += remove_file(join(root, fname),
                                           ignore_errors=ignore_errors, **kwargs)
        if not recursive:
            break
    print('[util_path] ... Removed %d/%d files' % (num_removed, num_matched))
    return True


def delete(path, dryrun=False, recursive=True, verbose=VERBOSE, print_exists=True, ignore_errors=True, **kwargs):
    """ Removes a file or directory """
    if not QUIET:
        print('[util_path] Deleting path=%r' % path)
    if not exists(path):
        if print_exists and not QUIET:
            msg = ('..does not exist!')
            print(msg)
        return False
    rmargs = dict(dryrun=dryrun, recursive=recursive, verbose=verbose,
                  ignore_errors=ignore_errors, **kwargs)
    if isdir(path):
        flag = remove_files_in_dir(path, **rmargs)
        flag = flag and remove_dirs(path, **rmargs)
    elif isfile(path):
        flag = remove_file(path, **rmargs)
    if not QUIET:
        print('[util_path] Finished deleting path=%r' % path)
    return flag


def remove_existing_fpaths(fpath_list, verbose=VERBOSE, quiet=QUIET,
                           strict=False, print_caller=PRINT_CALLER, lbl='files'):
    """ checks existance before removing. then tries to remove exisint paths """
    import utool as ut
    if print_caller:
        print(util_dbg.get_caller_name(range(1, 4)) + ' called remove_existing_fpaths')
    fpath_list_ = ut.filter_Nones(fpath_list)
    exists_list = list(map(exists, fpath_list_))
    if verbose:
        nTotal = len(fpath_list)
        nValid = len(fpath_list_)
        nExist = sum(exists_list)
        print('[util_path.remove_existing_fpaths] requesting delete of %d %s' % (nTotal, lbl))
        if nValid != nTotal:
            print('[util_path.remove_existing_fpaths] trying to delete %d/%d non None %s ' % (nValid, nTotal, lbl))
        print('[util_path.remove_existing_fpaths] %d/%d exist and need to be deleted' % (nExist, nValid))
    existing_fpath_list = ut.filter_items(fpath_list_, exists_list)
    return remove_fpaths(existing_fpath_list, verbose=verbose, quiet=quiet,
                            strict=strict, print_caller=False, lbl=lbl)


def remove_fpaths(fpath_list, verbose=VERBOSE, quiet=QUIET, strict=False, print_caller=PRINT_CALLER, lbl='files'):
    if print_caller:
        print(util_dbg.get_caller_name(range(1, 4)) + ' called remove_fpaths')
    nTotal = len(fpath_list)
    _verbose = (not quiet and nTotal > 0) or VERYVERBOSE
    if _verbose:
        print('[util_path.remove_fpaths] try removing %d %s' % (nTotal, lbl))
    nRemoved = 0
    for fpath in fpath_list:
        try:
            os.remove(fpath)  # Force refresh
            nRemoved += 1
        except OSError as ex:
            if VERYVERBOSE:
                print('WARNING: Could not remove fpath = %r' % (fpath,))
            if strict:
                util_dbg.printex(ex, 'Could not remove fpath = %r' % (fpath,), iswarning=False)
                raise
            pass
    if _verbose:
        print('[util_path.remove_fpaths] ... removed %d / %d %s' % (nRemoved, nTotal, lbl))
    return nRemoved


remove_file_list = remove_fpaths  # backwards compatible


def longest_existing_path(_path):
    """  Returns the longest root of _path that exists """
    while True:
        _path_new = os.path.dirname(_path)
        if exists(_path_new):
            _path = _path_new
            break
        if _path_new == _path:
            print('!!! This is a very illformated path indeed.')
            _path = ''
            break
        _path = _path_new
    return _path


def get_path_type(path_):
    """
    returns if a path is a file, directory, link, or mount
    """
    path_type = ''
    if isfile(path_):
        path_type += 'file'
    if isdir(path_):
        path_type += 'directory'
    if islink(path_):
        path_type += 'link'
    if ismount(path_):
        path_type += 'mount'
    return path_type


def checkpath(path_, verbose=VERYVERBOSE, n=None, info=VERYVERBOSE):
    """ verbose wrapper around ``os.path.exists``

    Returns:
        true if ``path_`` exists on the filesystem show only the top n directories

    Args:
        path_ (?):
        verbose (bool):  verbosity flag(default = False)
        n (None): (default = None)
        info (bool): (default = False)

    CommandLine:
        python -m utool.util_path --test-checkpath

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> path_ = ut.__file__
        >>> verbose = True
        >>> n = None
        >>> info = False
        >>> result = checkpath(path_, verbose, n, info)
        >>> print(result)
        True

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> path_ = ut.__file__ + 'foobar'
        >>> verbose = True
        >>> result = checkpath(path_, verbose, n=None, info=True)
        >>> print(result)
        False
    """
    assert isinstance(path_, six.string_types), 'path_=%r is not a string. type(path_) = %r' % (path_, type(path_))
    path_ = normpath(path_)
    if sys.platform.startswith('win32'):
        # convert back to windows style path if using unix style
        if path_.startswith('\\'):
            dirs = path_.split('\\')
            if len(dirs) > 1 and len(dirs[0]) == 0 and len(dirs[1]) == 1:
                dirs[1] = dirs[1].upper() + ':'
                path_ = '\\'.join(dirs[1:])
    does_exist = exists(path_)
    if verbose:
        #print_('[utool] checkpath(%r)' % (path_))
        pretty_path = path_ndir_split(path_, n)
        caller_name = util_dbg.get_caller_name(allow_genexpr=False)
        print('[%s] checkpath(%r)' % (caller_name, pretty_path))
        if does_exist:
            path_type = get_path_type(path_)
            #path_type = 'file' if isfile(path_) else 'directory'
            print('[%s] ...(%s) exists' % (caller_name, path_type,))
        else:
            print('[%s] ... does not exist' % (caller_name))
    if not does_exist and info:
        #print('[util_path]  ! Does not exist')
        _longest_path = longest_existing_path(path_)
        _longest_path_type = get_path_type(_longest_path)
        print('[util_path] ... The longest existing path is: %r' % _longest_path)
        print('[util_path] ... and has type %r' % (_longest_path_type,))
    return does_exist


def ensurepath(path_, verbose=VERYVERBOSE):
    """ DEPRICATE - alias - use ensuredir instead """
    return ensuredir(path_, verbose=verbose)


def ensuredir(path_, verbose=VERYVERBOSE, info=False, mode=0o1777):
    """ Ensures that directory will exist. creates new dir with sticky bits by default """
    if not checkpath(path_, verbose=verbose, info=info):
        if verbose:
            print('[util_path] mkdir(%r)' % path_)
        #os.makedirs(path_)
        try:
            os.makedirs(normpath(path_), mode=mode)
        except OSError as ex:
            util_dbg.printex(ex, 'check that the longest existing path is not a bad windows symlink.')
            raise
    return path_
    #return True


# ---File Copy---

def copy_worker(args):
    """ for util_parallel.generate """
    src, dst = args
    try:
        shutil.copy2(src, dst)
    except OSError:
        return False
    except shutil.Error:
        pass
    return True


def copy_files_to(src_fpath_list, dst_dpath=None, dst_fpath_list=None, overwrite=False, verbose=True, veryverbose=False):
    """
    parallel copier

    Example:
        >>> # DISTABLE_DOCTEST
        >>> from utool.util_path import *
        >>> import utool as ut
        >>> overwrite = False
        >>> veryverbose = False
        >>> verbose = True
        >>> src_fpath_list = [ut.grab_test_imgpath(key) for key in  ut.get_valid_test_imgkeys()]
        >>> dst_dpath = ut.get_app_resource_dir('utool', 'filecopy_tests')
        >>> copy_files_to(src_fpath_list, dst_dpath, overwrite=overwrite, verbose=verbose)
    """
    from utool import util_list
    from utool import util_parallel
    if verbose:
        print('[util_path] +--- COPYING FILES ---')
        print('[util_path]  * len(src_fpath_list) = %r' % (len(src_fpath_list)))
        print('[util_path]  * dst_dpath = %r' % (dst_dpath,))

    if dst_fpath_list is None:
        ensuredir(dst_dpath, verbose=veryverbose)
        dst_fpath_list = [join(dst_dpath, basename(fpath)) for fpath in src_fpath_list]
    else:
        assert dst_dpath is None, 'dst_dpath was specified but overrided'
        assert len(dst_fpath_list) == len(src_fpath_list), 'bad correspondence'

    exists_list = list(map(exists, dst_fpath_list))
    if verbose:
        print('[util_path]  * %d files already exist dst_dpath' % (sum(exists_list),))
    if not overwrite:
        dst_fpath_list_ = util_list.filterfalse_items(dst_fpath_list, exists_list)
        src_fpath_list_ = util_list.filterfalse_items(src_fpath_list, exists_list)
    else:
        dst_fpath_list_ = dst_fpath_list
        src_fpath_list_ = src_fpath_list

    success_list = list(util_parallel.generate(copy_worker, zip(src_fpath_list_, dst_fpath_list_), nTasks=len(src_fpath_list_)))

    #success_list = copy_list(src_fpath_list_, dst_fpath_list_)
    if verbose:
        print('[util_path]  * Copied %d / %d' % (sum(success_list), len(src_fpath_list)))
        print('[util_path] L___ DONE COPYING FILES ___')


def copy(src, dst, overwrite=True, deeplink=True, verbose=True, dryrun=False):
    import utool as ut
    if ut.isiterable(src):
        if not ut.isiterable(dst):
            # list to non list
            ut.copy_files_to(src, dst, overwrite=overwrite, verbose=verbose)
        else:
            # list to list
            ut.copy_files_to(src, dst_fpath_list=dst, overwrite=overwrite, verbose=verbose)
    else:
        return copy_single(src, dst, overwrite=overwrite, deeplink=deeplink, dryrun=dryrun, verbose=verbose)


def copy_single(src, dst, overwrite=True, verbose=True, deeplink=True, dryrun=False):
    """
    Args:
        src (str): file or directory to copy
        dst (str): directory or new file to copy to

    Copies src file or folder to dst.

    If src is a folder this copy is recursive.
    """
    try:
        if exists(src):
            if not isdir(src) and isdir(dst):
                # copying file to directory
                dst = join(dst, basename(src))
            if exists(dst):
                if overwrite:
                    prefix = 'C+O'
                    if verbose:
                        print('[util_path] [Copying + Overwrite]:')
                else:
                    prefix = 'Skip'
                    if verbose:
                        print('[%s] ->%s' % (prefix, dst))
                    return
            else:
                prefix = 'C'
                if verbose:
                    if dryrun:
                        print('[util_path] [DryRun]: ')
                    else:
                        print('[util_path] [Copying]: ')
            if verbose:
                print('[%s] | %s' % (prefix, src))
                print('[%s] ->%s' % (prefix, dst))
            if not dryrun:
                if not deeplink and islink(src):
                    linkto = os.readlink(src)
                    symlink(linkto, dst)
                elif isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        else:
            prefix = 'Miss'
            if verbose:
                print('[util_path] [Cannot Copy]: ')
                print('[%s] src=%s does not exist!' % (prefix, src))
                print('[%s] dst=%s' % (prefix, dst))
    except Exception as ex:
        import utool as ut
        ut.printex(ex, 'Error copying single', keys=['src', 'dst'])
        raise


def copy_all(src_dir, dest_dir, glob_str_list, recursive=False):
    ensuredir(dest_dir)
    if not isinstance(glob_str_list, list):
        glob_str_list = [glob_str_list]
    for root, dirs, files in os.walk(src_dir):
        for dname_ in dirs:
            for glob_str in glob_str_list:
                if fnmatch.fnmatch(dname_, glob_str):
                    src = normpath(join(src_dir, dname_))
                    dst = normpath(join(dest_dir, dname_))
                    ensuredir(dst)
        for fname_ in files:
            for glob_str in glob_str_list:
                if fnmatch.fnmatch(fname_, glob_str):
                    src = normpath(join(src_dir, fname_))
                    dst = normpath(join(dest_dir, fname_))
                    copy(src, dst)
        if not recursive:
            break


def copy_list(src_list, dst_list, lbl='Copying',
              ioerr_ok=False, sherro_ok=False, oserror_ok=False):
    """ Copies all data and stat info """
    # Feb - 6 - 2014 Copy function
    import utool as ut
    task_iter = zip(src_list, dst_list)
    def docopy(src, dst):
        try:
            shutil.copy2(src, dst)
        except OSError:
            if ioerr_ok:
                return False
            raise
        except shutil.Error:
            if sherro_ok:
                return False
            raise
        except IOError:
            if ioerr_ok:
                return False
            raise
        return True
    success_list = [
        docopy(src, dst)
        for (src, dst) in ut.ProgressIter(task_iter, adjust=True, lbl=lbl)]
    return success_list


def move(src, dst, lbl='Moving'):
    return move_list([src], [dst], lbl)


def move_list(src_list, dst_list, lbl='Moving'):
    # Feb - 6 - 2014 Move function
    def domove(src, dst, count):
        try:
            shutil.move(src, dst)
        except OSError:
            return False
        mark_progress(count)
        return True
    task_iter = zip(src_list, dst_list)
    mark_progress, end_progress = progress_func(len(src_list), lbl=lbl)
    success_list = [domove(src, dst, count) for count, (src, dst) in enumerate(task_iter)]
    end_progress()
    return success_list


def win_shortcut(source, link_name):
    """
    Attempt to create windows shortcut
    TODO: TEST / FIXME

    References:
        http://stackoverflow.com/questions/1447575/symlinks-on-windows
    """
    if True:
        import ctypes
        kdll = ctypes.windll.LoadLibrary("kernel32.dll")
        code = 1 if isdir(source) else 0
        kdll.CreateSymbolicLinkA(source, link_name, code)
    else:
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if isdir(source) else 0
        retval = csl(link_name, source, flags)
        if retval == 0:
            #warn_msg = '[util_path] Unable to create symbolic link on windows.'
            #print(warn_msg)
            #warnings.warn(warn_msg, category=UserWarning)
            if checkpath(link_name):
                return True
            raise ctypes.WinError()


def symlink(path, link, noraise=False):
    """
    Attempt to create unix or windows symlink
    TODO: TEST / FIXME

    Args:
        path (str): path to real file or directory
        link (str): path to desired location for symlink
        noraise (bool):

    """
    path = normpath(path)
    link = normpath(link)
    if os.path.islink(link):
        print('[util_path] symlink %r exists' % (link))
        return
    print('[util_path] Creating symlink: path=%r link_name=%r' % (path, link))
    try:
        os_symlink = getattr(os, "symlink", None)
        if callable(os_symlink):
            os_symlink(path, link)
        else:
            win_shortcut(path, link)
    except Exception as ex:
        checkpath(link, True)
        checkpath(path, True)
        import utool as ut
        ut.printex(ex, 'error making symlink', iswarning=noraise)
        if not noraise:
            raise


def file_bytes(fpath):
    r"""
    returns size of file in bytes (int)
    """
    return os.stat(fpath).st_size


def file_megabytes(fpath):
    r"""
    returns size of file in megabytes (float)
    """
    return os.stat(fpath).st_size / (2.0 ** 20)


def glob_python_modules(dirname, **kwargs):
    return glob(dirname, '*.py', recursive=True, with_dirs=False)


def glob(dpath, pattern, recursive=False, with_files=True, with_dirs=True,
         maxdepth=None, exclude_dirs=[], fullpath=True, **kwargs):
    r"""
    Globs directory for pattern

    Args:
        dpath (str):  directory path
        pattern (str):
        recursive (bool): (default = False)
        with_files (bool): (default = True)
        with_dirs (bool): (default = True)
        maxdepth (None): (default = None)
        exclude_dirs (list): (default = [])

    Returns:
        list: path_list

    SeeAlso:
        iglob

    CommandLine:
        python -m utool.util_path --test-glob

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> from os.path import dirname
        >>> dpath = dirname(ut.__file__)
        >>> pattern = '__*.py'
        >>> recursive = True
        >>> with_files = True
        >>> with_dirs = True
        >>> maxdepth = None
        >>> fullpath = False
        >>> exclude_dirs = ['_internal', join(dpath, 'experimental')]
        >>> print('exclude_dirs = ' + ut.list_str(exclude_dirs))
        >>> path_list = glob(dpath, pattern, recursive, with_files, with_dirs, maxdepth, exclude_dirs, fullpath)
        >>> result = ('path_list = %s' % (ut.list_str(path_list),))
        >>> result = result.replace(r'\\', '/')
        >>> print(result)
        path_list = [
            '__init__.py',
            'tests/__init__.py',
        ]
    """
    if dpath.find('*') >= 0:
        print('warning: star in dpath. should be in pattern')
    gen = iglob(dpath, pattern, recursive=recursive,
                with_files=with_files, with_dirs=with_dirs, maxdepth=maxdepth,
                fullpath=fullpath, exclude_dirs=exclude_dirs, **kwargs)
    path_list = list(gen)
    return path_list


def iglob(dpath, pattern, recursive=False, with_files=True, with_dirs=True,
          maxdepth=None, exclude_dirs=[], fullpath=True, **kwargs):
    r"""
    Iteratively globs directory for pattern

    Args:
        dpath (str):  directory path
        pattern (str):
        recursive (bool): (default = False)
        with_files (bool): (default = True)
        with_dirs (bool): (default = True)
        maxdepth (None): (default = None)
        exclude_dirs (list): (default = [])

    Yields:
        path
    """
    if kwargs.get('verbose', False):  # log what i'm going to do
        print('[util_path] glob(dpath=%r)' % truepath(dpath,))
    nFiles = 0
    nDirs  = 0
    current_depth = 0
    dpath_ = truepath(dpath)
    posx1 = len(dpath_) + len(os.path.sep)
    #exclude_dirs_rel = [relpath(dpath_, dir_) for dir_ in exclude_dirs]
    #exclude_dirs_rel = [relpath(dpath_, dir_) for dir_ in exclude_dirs]
    #print('\n\n\n')
    #import utool as ut
    #print('exclude_dirs = %s' % (ut.list_str(exclude_dirs),))
    for root, dirs, files in os.walk(dpath_, topdown=True):
        # Modifying dirs in-place will prune the subsequent files and directories visitied by os.walk
        # References: http://stackoverflow.com/questions/19859840/excluding-directories-in-os-walk
        rel_root = relpath(root, dpath_)
        rel_root2 = relpath(root, dirname(dpath_))
        #print('rel_root = %r' % (rel_root,))
        #if len(dirs) > 0:
        #    print('dirs = %s' % (ut.list_str([join(rel_root, d) for d in dirs]),))
        if len(exclude_dirs) > 0:
            dirs[:] = [d for d in dirs if normpath(join(rel_root, d)) not in exclude_dirs]
            # hack
            dirs[:] = [d for d in dirs if normpath(join(rel_root2, d)) not in exclude_dirs]
            # check abs path as well
            dirs[:] = [d for d in dirs if normpath(join(root, d)) not in exclude_dirs]

        # yeild data
        # print it only if you want
        if maxdepth is not None:
            current_depth = root[posx1:].count(os.path.sep)
            if maxdepth <= current_depth:
                continue
        #print('-----------')
        #print(current_depth)
        #print(root)
        #print('==')
        #print(dirs)
        #print('-----------')
        if with_files:
            for fname in fnmatch.filter(files, pattern):
                nFiles += 1
                fpath = join(root, fname)
                if fullpath:
                    yield fpath
                else:
                    yield relpath(fpath, dpath_)

        if with_dirs:
            for dname in fnmatch.filter(dirs, pattern):
                dpath = join(root, dname)
                nDirs += 1
                if fullpath:
                    yield dpath
                else:
                    yield relpath(dpath, dpath_)
        if not recursive:
            break
    if kwargs.get('verbose', False):  # log what i've done
        nTotal = nDirs + nFiles
        print('[util_path] Found: %d' % (nTotal))


# --- Images ----

def num_images_in_dir(path):
    """
    returns the number of images in a directory
    """
    num_imgs = 0
    for root, dirs, files in os.walk(path):
        for fname in files:
            if matches_image(fname):
                num_imgs += 1
    return num_imgs


def matches_image(fname):
    """ returns true if a filename matches an image pattern """
    fname_ = fname.lower()
    img_pats = ['*' + ext for ext in IMG_EXTENSIONS]
    return any([fnmatch.fnmatch(fname_, pat) for pat in img_pats])


def dirsplit(path):
    return path.split(os.sep)


def fpaths_to_fnames(fpath_list):
    """
    Args:
        fpath_list (list of strs): list of file-paths
    Returns:
        fname_list (list of strs): list of file-names
    """
    fname_list = [split(fpath)[1] for fpath in fpath_list]
    return fname_list


def fnames_to_fpaths(fname_list, path):
    fpath_list = [join(path, fname) for fname in fname_list]
    return fpath_list


def get_modpath_from_modname(modname):
    r"""
    Args:
        modname (str):

    Returns:
        str: module_dir

    CommandLine:
        python -m utool.util_path --test-get_modpath_from_modname

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> modname = 'utool.util_path'
        >>> module_dir = get_modpath_from_modname(modname)
        >>> result = str(module_dir)
        >>> print(result)
    """
    import importlib
    module = importlib.import_module(modname)
    modpath = module.__file__.replace('.pyc', '.py')
    #modname = modname.replace('.__init__', '').strip()
    #module_dir = get_module_dir(module)
    return modpath


def get_module_dir(module, *args):
    module_dir = truepath(dirname(module.__file__))
    if len(args) > 0:
        module_dir = join(module_dir, *args)
    return module_dir


def ensure_unixslash(path):
    return path.replace('\\', '/')


def ensure_crossplat_path(path, winroot='C:'):
    r"""
    ensure_crossplat_path

    Args:
        path (str):

    Returns:
        str: crossplat_path

    Example(DOCTEST):
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> path = r'C:\somedir'
        >>> cplat_path = ensure_crossplat_path(path)
        >>> result = cplat_path
        >>> print(result)
        C:/somedir
    """
    cplat_path = path.replace('\\', '/')
    if cplat_path == winroot:
        cplat_path += '/'
    return cplat_path


def ensure_native_path(path, winroot='C:'):
    import utool as ut
    if ut.WIN32 and path.startswith('/') or  path.startswith('\\'):
        path = winroot + path


def get_relative_modpath(module_fpath):
    """
    Returns path to module relative to the package root

    Args:
        module_fpath (str): module filepath

    Returns:
        str: modname

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> module_fpath = ut.util_path.__file__
        >>> rel_modpath = ut.get_relative_modpath(module_fpath)
        >>> rel_modpath = rel_modpath.replace('.pyc', '.py')  # allow pyc or py
        >>> result = ensure_crossplat_path(rel_modpath)
        >>> print(result)
        utool/util_path.py
    """
    modsubdir_list = get_module_subdir_list(module_fpath)
    _, ext = splitext(module_fpath)
    rel_modpath = join(*modsubdir_list) + ext
    rel_modpath = ensure_crossplat_path(rel_modpath)
    return rel_modpath


def get_modname_from_modpath(module_fpath):
    """
    returns importable name from file path

    get_modname_from_modpath

    Args:
        module_fpath (str): module filepath

    Returns:
        str: modname

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> module_fpath = ut.util_path.__file__
        >>> modname = ut.get_modname_from_modpath(module_fpath)
        >>> result = modname
        >>> print(result)
        utool.util_path
    """
    modsubdir_list = get_module_subdir_list(module_fpath)
    modname = '.'.join(modsubdir_list)
    modname = modname.replace('.__init__', '').strip()
    return modname


def get_module_subdir_list(module_fpath):
    """
    get_module_subdir_list

    Args:
        module_fpath (str):

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> module_fpath = ut.util_path.__file__
        >>> modsubdir_list = get_module_subdir_list(module_fpath)
        >>> result = modsubdir_list
        >>> print(result)
        ['utool', 'util_path']
    """
    module_fpath = truepath(module_fpath)
    dpath, fname_ext = split(module_fpath)
    fname, ext = splitext(fname_ext)
    full_dpath = dpath
    dpath = full_dpath
    _modsubdir_list = [fname]
    while is_module_dir(dpath):
        dpath, dname = split(dpath)
        _modsubdir_list.append(dname)
    modsubdir_list = _modsubdir_list[::-1]
    return modsubdir_list


def ls(path, pattern='*'):
    """ like unix ls - lists all files and dirs in path"""
    path_iter = glob(path, pattern, recursive=False)
    return sorted(list(path_iter))


def ls_dirs(path, pattern='*'):
    dir_iter = list(glob(path, pattern, recursive=False, with_files=False))
    return sorted(list(dir_iter))


def ls_modulefiles(path, private=True, full=True, noext=False):
    module_file_list = ls(path, '*.py')
    module_file_iter = iter(module_file_list)
    if not private:
        module_file_iter = filterfalse(is_private_module, module_file_iter)
    if not full:
        module_file_iter = map(basename, module_file_iter)
    if noext:
        module_file_iter = (splitext(path)[0] for path in module_file_iter)
    return list(module_file_iter)


def ls_moduledirs(path, private=True, full=True):
    """ lists all dirs which are python modules in path """
    dir_list = ls_dirs(path)
    module_dir_iter = filter(is_module_dir, dir_list)
    if not private:
        module_dir_iter = filterfalse(is_private_module, module_dir_iter)
    if not full:
        module_dir_iter = map(basename, module_dir_iter)
    return list(module_dir_iter)


def get_basename_noext_list(path_list):
    return [basename_noext(path) for path in path_list]


def get_ext_list(path_list):
    return [splitext(path)[1] for path in path_list]


def get_basepath_list(path_list):
    return [split(path)[0] for path in path_list]


def basename_noext(path):
    return splitext(basename(path))[0]


def append_suffixlist_to_namelist(name_list, suffix_list):
    """ adds a suffix to the path before the extension
    if name_list is a path_list the basepath is stripped away """
    assert len(name_list) == len(suffix_list)
    #basepath_list  = utool.get_basepath_list(name_list)
    gnamenoext_list = get_basename_noext_list(name_list)
    ext_list        = get_ext_list(name_list)
    new_name_list   = [name + suffix + ext for name, suffix, ext in
                        zip(gnamenoext_list, suffix_list, ext_list)]
    return new_name_list


def is_private_module(path):
    return basename(path).startswith('__')


def is_module_dir(path):
    """
    Args:
        path (str)

    Returns:
        flag: True if path contains an __init__ file

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> path = truepath('~/code/utool/utool')
        >>> flag = is_module_dir(path)
        >>> result = (flag)
        >>> print(result)
    """
    return exists(join(path, '__init__.py'))


def list_images(img_dpath_, ignore_list=[], recursive=False, fullpath=False,
                full=None, sort=True):
    """ TODO: rename to ls_images
        TODO: Change all instances of fullpath to full
    """
    #if not QUIET:
    #    print(ignore_list)
    if full is not None:
        fullpath = fullpath or full
    img_dpath = realpath(img_dpath_)
    ignore_set = set(ignore_list)
    gname_list_ = []
    assertpath(img_dpath)
    # Get all the files in a directory recursively
    for root, dlist, flist in os.walk(truepath(img_dpath)):
        rel_dpath = relpath(root, img_dpath)
        # Ignore directories
        if any([dname in ignore_set for dname in dirsplit(rel_dpath)]):
            continue
        for fname in iter(flist):
            gname = join(rel_dpath, fname).replace('\\', '/').replace('./', '')
            if matches_image(gname):
                # Ignore Files
                if gname in ignore_set:
                    continue
                if fullpath:
                    gpath = join(img_dpath, gname)
                    gname_list_.append(gpath)
                else:
                    gname_list_.append(gname)
        if not recursive:
            break
    # Filter out non images or ignorables
    #gname_list = [gname_ for gname_ in iter(gname_list_)
    #              if gname_ not in ignore_set and matches_image(gname_)]
    if sort:
        gname_list = sorted(gname_list_)
    return gname_list


def assertpath(path_, msg='', **kwargs):
    """ Asserts that a patha exists """
    if NO_ASSERTS:
        return
    if path_ is None:
        raise AssertionError('path is None! %s' % (path_, msg))
    if path_ == '':
        raise AssertionError('path=%r is the empty string! %s' % (path_, msg))
    if not checkpath(path_, **kwargs):
        raise AssertionError('path=%r does not exist! %s' % (path_, msg))


assert_exists = assertpath
#def assert_exists(path, msg='', **kwargs):
#    if NO_ASSERTS:
#        return
#    return assertpath(path, msg, **kwargs)
#    #assert exists(path), 'path=%r does not exist! %s' % (path, msg)


def grepfile(fpath, regexpr_list, reflags=0):
    """
    grepfile - greps a specific file

    Args:
        fpath (str):
        regexpr_list (list or str): pattern or list of patterns

    Returns:
        tuple (list, list): list of lines and list of line numbers

    Example:
        >>> import utool as ut
        >>> fpath = ut.truepath('~/code/ibeis/ibeis/model/hots/smk/smk_match.py')
        >>> regexpr_list = ['get_argflag', 'get_argval']
        >>> result = ut.grepfile(fpath, regexpr_list)
        >>> print(result)
    """
    found_lines = []
    found_lxs = []
    # Ensure a list
    islist = isinstance(regexpr_list, (list, tuple))
    regexpr_list_ = regexpr_list if islist else [regexpr_list]
    # Open file and search lines
    with open(fpath, 'r') as file_:
        line_list = file_.readlines()
        # Search each line for each pattern
        for lx, line in enumerate(line_list):
            for regexpr_ in regexpr_list_:
                # FIXME: multiline mode doesnt work
                match_object = re.search(regexpr_, line, flags=reflags)
                if match_object is not None:
                    found_lines.append(line)
                    found_lxs.append(lx)
    return found_lines, found_lxs


def pathsplit_full(path):
    """ splits all directories in path into a list """
    return path.replace('\\', '/').split('/')


def get_standard_exclude_dnames():
    return ['lib.linux-x86_64-2.7', 'dist', 'build', '_page', '_doc', 'utool.egg-info', '.git']


def get_standard_include_patterns():
    return ['*.py', '*.cxx', '*.cpp', '*.hxx', '*.hpp', '*.c', '*.h', '*.vim']


def matching_fnames(dpath_list, include_patterns, exclude_dirs=[],
                    greater_exclude_dirs=[], recursive=True):
    """

    # TODO: fix names and behavior of exclude_dirs and greater_exclude_dirs

    matching_fnames. walks dpath lists returning all directories that match the
    requested pattern.

    Args:
        dpath_list       (list):
        include_patterns (?):
        exclude_dirs     (None):
        recursive        (bool):

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> dpath_list = [dirname(dirname(ut.__file__))]
        >>> include_patterns = get_standard_include_patterns()
        >>> exclude_dirs = ['_page']
        >>> greater_exclude_dirs = get_standard_exclude_dnames()
        >>> recursive = True
        >>> fpath_gen = matching_fnames(dpath_list, include_patterns, exclude_dirs, greater_exclude_dirs, recursive)
        >>> result = list(fpath_gen)
        >>> print('\n'.join(result))
    """
    if isinstance(dpath_list, six.string_types):
        dpath_list = [dpath_list]
    for dpath in dpath_list:
        for root, dname_list, fname_list in os.walk(dpath):
            # Look at all subdirs
            subdirs = pathsplit_full(relpath(root, dpath))
            # HACK:
            if any([dir_ in greater_exclude_dirs for dir_ in subdirs]):
                continue
            # Look at one subdir
            if basename(root) in exclude_dirs:
                continue
            for name in fname_list:
                # For the filesnames which match the patterns
                if any([fnmatch.fnmatch(name, pat) for pat in include_patterns]):
                    yield join(root, name)
                    #fname_list.append((root, name))
            if not recursive:
                break
    #return fname_list


def grep(regex_list, recursive=True, dpath_list=None, include_patterns=None,
         exclude_dirs=[], greater_exclude_dirs=None,
         inverse=False, verbose=VERBOSE, fpath_list=None, reflags=0):
    """
    Python implementation of grep. NOT FINISHED

    greps for patterns

    Args:
        regex_list (str or list): one or more patterns to find
        recursive (bool):
        dpath_list (list): directories to search (defaults to cwd)
        include_patterns (list) : defaults to standard file extensions

    Returns:
        tuple (list, list, list): (found_fpath_list, found_lines_list, found_lxs_list)

    Example:
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> dpath_list = [ut.truepath('~/code/ibeis/ibeis')]
        >>> include_patterns = ['*.py']
        >>> exclude_dirs = []
        >>> regex_list = ['get_argflag', 'get_argval']
        >>> verbose = False
        >>> recursive = True
        >>> result = ut.grep(regex_list, recursive, dpath_list, include_patterns, exclude_dirs)
        >>> (found_fpath_list, found_lines_list, found_lxs_list) = result
        >>> print(result)

    """
    if include_patterns is None:
        include_patterns =  get_standard_include_patterns()
    if greater_exclude_dirs is None:
        greater_exclude_dirs =  get_standard_exclude_dnames()
    # ensure list input
    if isinstance(include_patterns, six.string_types):
        include_patterns = [include_patterns]
    if dpath_list is None:
        dpath_list = [os.getcwd()]
    if verbose:
        recursive_stat_str = ['flat', 'recursive'][recursive]
        print('[util_path] Greping (%s) %r for %r' % (recursive_stat_str, dpath_list, regex_list))
    if isinstance(regex_list, six.string_types):
        regex_list = [regex_list]
    found_fpath_list = []
    found_lines_list = []
    found_lxs_list = []
    # Walk through each directory recursively
    if fpath_list is None:
        fpath_generator = matching_fnames(dpath_list, include_patterns, exclude_dirs, greater_exclude_dirs, recursive=recursive)
    else:
        fpath_generator = fpath_list
    extended_regex_list = list(map(extend_regex, regex_list))
    # For each matching filepath
    for fpath in fpath_generator:
        # For each search pattern
        found_lines, found_lxs = grepfile(fpath, extended_regex_list, reflags)
        if inverse:
            if len(found_lines) == 0:
                # Append files that the pattern was not found in
                found_fpath_list.append(fpath)
                found_lines_list.append([])
                found_lxs_list.append([])
        elif len(found_lines) > 0:
            found_fpath_list.append(fpath)  # regular matching
            found_lines_list.append(found_lines)
            found_lxs_list.append(found_lxs)
    if verbose:
        print('==========')
        print('==========')
        print('[util_path] found matches in %d files' % len(found_fpath_list))

        for fpath, found, lxs in zip(found_fpath_list, found_lines_list, found_lxs_list):
            if len(found) > 0:
                print('----------------------')
                print('Found %d line(s) in %r: ' % (len(found), fpath))
                name = split(fpath)[1]
                max_line = len(lxs)
                ndigits = str(len(str(max_line)))
                fmt_str = '%s : %' + ndigits + 'd |%s'
                for (lx, line) in zip(lxs, found):
                    print(fmt_str % (name, lx, line))

        #print('[util_path] found matches in %d files' % len(found_fpath_list))
    return found_fpath_list, found_lines_list, found_lxs_list


def get_win32_short_path_name(long_name):
    """
    Gets the short path name of a given long path.

    References:
        http://stackoverflow.com/a/23598461/200291
        http://stackoverflow.com/questions/23598289/how-to-get-windows-short-file-name-in-python

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut  # NOQA
        >>> # build test data
        >>> #long_name = unicode(normpath(ut.get_resource_dir()))
        >>> long_name = unicode(r'C:/Program Files (x86)')
        >>> #long_name = unicode(r'C:/Python27')
        #unicode(normpath(ut.get_resource_dir()))
        >>> # execute function
        >>> result = get_win32_short_path_name(long_name)
        >>> # verify results
        >>> print(result)
        C:/PROGRA~2
    """
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            short_name = output_buf.value
            break
        else:
            output_buf_size = needed
    return short_name


def fixwin32_shortname(path1):
    try:
        #try:
        #    import win32file
        #    path2 = win32file.GetLongPathName(path1)
        #except ImportError:
            import ctypes
            #import win32file
            path1 = unicode(path1)
            buflen = 260  # max size
            buf = ctypes.create_unicode_buffer(buflen)
            ctypes.windll.kernel32.GetLongPathNameW(path1, buf, buflen)
            # If the path doesnt exist windows doesnt return anything
            path2 = buf.value if len(buf.value) > 0 else path1
    except Exception as ex:
        print(ex)
        util_dbg.printex(ex, 'cannot fix win32 shortcut', keys=['path1', 'path2'])
        path2 = path1
        #raise
    return path2


def platform_path(path):
    r"""
    Returns platform specific path for pyinstaller usage

    Args:
        path (str):

    Returns:
        str: path2

    CommandLine:
        python -m utool.util_path --test-platform_path

    Example:
        >>> # ENABLE_DOCTEST
        >>> # FIXME: find examples of the wird paths this fixes (mostly on win32 i think)
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut
        >>> path = 'some/odd/../weird/path'
        >>> path2 = platform_path(path)
        >>> result = str(path2)
        >>> if ut.WIN32:
        ...     ut.assert_eq(path2, r'some\weird\path')
        ... else:
        ...     ut.assert_eq(path2, r'some/weird/path')

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> import utool as ut    # NOQA
        >>> if ut.WIN32:
        ...     path = 'C:/PROGRA~2'
        ...     path2 = platform_path(path)
        ...     assert path2 == u'..\\..\\..\\..\\Program Files (x86)'
    """
    try:
        if path == '':
            raise ValueError('path cannot be the empty string')
        # get path relative to cwd
        path1 = truepath_relative(path)
        if sys.platform.startswith('win32'):
            path2 = fixwin32_shortname(path1)
        else:
            path2 = path1
    except Exception as ex:
        util_dbg.printex(ex, keys=['path', 'path1', 'path2'])
        raise
    return path2


def existing_subpath(root_path, valid_subpaths, tiebreaker='first', verbose=VERYVERBOSE):
    """
    Returns join(root_path, subpath) where subpath in valid_subpath ane
    exists(subpath)
    """
    # Find the oxford_style groundtruth directory
    for subpath in valid_subpaths:
        path  = join(root_path, subpath)
        if checkpath(path, verbose=verbose):
            if tiebreaker == 'first':
                return path
    raise AssertionError('none of the following subpaths exist: %r' %
                         (valid_subpaths,))


#def find_executable(exename):
#    import utool as ut
#    search_dpaths = ut.get_install_dirs()
#    pass


def search_in_dirs(fname, search_dpaths=[], shortcircuit=True,
                   return_tried=False, strict=False):
    """
    search_in_dirs

    Args:
        fname (?):
        search_dpaths (list):
        shortcircuit (bool):
        return_tried(bool): return tried paths

    Returns:
        fpath: None

    Example:
        >>> import utool as ut
        >>> fname = 'Inno Setup 5\ISCC.exe'
        >>> search_dpaths = ut.get_install_dirs()
        >>> shortcircuit = True
        >>> fpath = ut.search_in_dirs(fname, search_dpaths, shortcircuit)
        >>> print(fpath)
    """
    fpath_list = []
    tried_list = []
    for dpath in search_dpaths:
        fpath = join(dpath, fname)
        if return_tried:
            tried_list.append(fpath)
        if exists(fpath):
            if shortcircuit:
                if return_tried:
                    return fpath, tried_list
                return fpath
            else:
                fpath_list.append(fpath)
    if strict and len(fpath_list) == 0:
        msg = ('Cannot find: fname=%r\n'  % (fname,))
        if return_tried:
            msg += 'Tried: \n    ' + '\n    '.join(tried_list)
        raise Exception(msg)

    if shortcircuit:
        if return_tried:
            return None, tried_list
        return None
    else:
        if return_tried:
            return fpath_list, tried_list
        return fpath_list


def find_lib_fpath(libname, root_dir, recurse_down=True, verbose=False, debug=False):
    """ Search for the library """

    def get_lib_fname_list(libname):
        """
        input <libname>: library name (e.g. 'hesaff', not 'libhesaff')
        returns <libnames>: list of plausible library file names
        """
        if sys.platform.startswith('win32'):
            libnames = ['lib' + libname + '.dll', libname + '.dll']
        elif sys.platform.startswith('darwin'):
            libnames = ['lib' + libname + '.dylib']
        elif sys.platform.startswith('linux'):
            libnames = ['lib' + libname + '.so']
        else:
            raise Exception('Unknown operating system: %s' % sys.platform)
        return libnames

    def get_lib_dpath_list(root_dir):
        """
        input <root_dir>: deepest directory to look for a library (dll, so, dylib)
        returns <libnames>: list of plausible directories to look.
        """
        'returns possible lib locations'
        get_lib_dpath_list = [root_dir,
                              join(root_dir, 'lib'),
                              join(root_dir, 'build'),
                              join(root_dir, 'build', 'lib')]
        return get_lib_dpath_list

    lib_fname_list = get_lib_fname_list(libname)
    tried_fpaths = []
    while root_dir is not None:
        for lib_fname in lib_fname_list:
            for lib_dpath in get_lib_dpath_list(root_dir):
                lib_fpath = normpath(join(lib_dpath, lib_fname))
                if exists(lib_fpath):
                    if verbose:
                        print('\n[c] Checked: '.join(tried_fpaths))
                    if debug:
                        print('using: %r' % lib_fpath)
                    return lib_fpath
                else:
                    # Remember which candiate library fpaths did not exist
                    tried_fpaths.append(lib_fpath)
            _new_root = dirname(root_dir)
            if _new_root == root_dir:
                root_dir = None
                break
            else:
                root_dir = _new_root
        if not recurse_down:
            break

    msg = ('\n[C!] load_clib(libname=%r root_dir=%r, recurse_down=%r, verbose=%r)' %
           (libname, root_dir, recurse_down, verbose) +
           '\n[c!] Cannot FIND dynamic library')
    print(msg)
    print('\n[c!] Checked: '.join(tried_fpaths))
    raise ImportError(msg)


def ensure_mingw_drive(win32_path):
    r""" replaces windows drives with mingw style drives

    Args:
        path (?):

    CommandLine:
        python -m utool.util_path --test-ensure_mingw_drive

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> win32_path = r'C:/Program Files/Foobar'
        >>> result = ensure_mingw_drive(win32_path)
        >>> print(result)
        /c/Program Files/Foobar
    """
    win32_drive, _path = splitdrive(win32_path)
    mingw_drive = '/' + win32_drive[:-1].lower()
    mingw_path = mingw_drive + _path
    return mingw_path


class ChdirContext(object):
    """
    References http://www.astropython.org/snippet/2009/10/chdir-context-manager
    """
    def __init__(self, dpath=None, stay=False):
        self.stay = stay
        self.curdir = os.getcwd()
        self.dpath = dpath

    def __enter__(self):
        if self.dpath is not None:
            print('Change directory to %r' % (self.dpath,))
            os.chdir(self.dpath)
        return self

    def __exit__(self, type_, value, trace):
        if not self.stay:
            print('Change directory to %r' % (self.curdir,))
            os.chdir(self.curdir)
        if trace is not None:
            if VERBOSE:
                print('[util_path] Error in chdir context manager!: ' + str(value))
            return False  # return a falsey value on error


def search_candidate_paths(candidate_path_list, candidate_name_list=None, priority_paths=None, required_subpaths=[], verbose=not QUIET):
    """
    searches for existing paths that meed a requirement

    Args:
        candidate_path_list (list): list of paths to check. If candidate_name_list is specified this is the dpath list instead
        candidate_name_list (list): specifies several names to check (default = None)
        priority_paths (None): specifies paths to check first. Ignore candidate_name_list (default = None)
        required_subpaths (list): specified required directory structure (default = [])
        verbose (bool):  verbosity flag(default = True)

    Returns:
        str: return_path

    CommandLine:
        python -m utool.util_path --test-search_candidate_paths

    Example:
        >>> # DISABLE_DOCTEST
        >>> from utool.util_path import *  # NOQA
        >>> candidate_path_list = [ut.truepath('~/RPI/code/utool'), ut.truepath('~/code/utool')]
        >>> candidate_name_list = None
        >>> required_subpaths = []
        >>> verbose = True
        >>> priority_paths = None
        >>> return_path = search_candidate_paths(candidate_path_list, candidate_name_list, priority_paths, required_subpaths, verbose)
        >>> result = ('return_path = %s' % (str(return_path),))
        >>> print(result)
    """
    print('Searching for candidate paths')
    import utool as ut
    from os.path import join, exists
    import itertools

    if candidate_name_list is not None:
        candidate_path_list_ = [join(dpath, fname) for dpath, fname in itertools.product(candidate_path_list, candidate_name_list)]
    else:
        candidate_path_list_ = candidate_path_list

    if priority_paths is not None:
        candidate_path_list_ = priority_paths + candidate_path_list_

    return_path = None
    for path in candidate_path_list_:
        if path is not None and exists(path):
            if verbose:
                print('Found candidate tomcat directory %r' % (path,))
                print('Checking for approprate structure')
            # tomcat directory exists. Make sure it also contains a webapps dir
            subpath_list = [join(path, subpath) for subpath in required_subpaths]
            if all(ut.checkpath(path_, verbose=verbose) for path_ in subpath_list):
                return_path = path
                if verbose:
                    print('Candidate path meets citera. Returning')
                return return_path
                break
    print('Did not find any candidates')
    return return_path


if __name__ == '__main__':
    """
    CommandLine:
        python -c "import utool, utool.util_path; utool.doctest_funcs(utool.util_path, allexamples=True)"
        python -m utool.util_path
        python -m utool.util_path --allexamples
        python -m utool.util_path --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
