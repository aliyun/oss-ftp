import contextlib
import importlib
import os
import sys
import unittest

from test.test_importlib import util

# needed tests:
#
# need to test when nested, so that the top-level path isn't sys.path
# need to test dynamic path detection, both at top-level and nested
# with dynamic path, check when a loader is returned on path reload (that is,
#  trying to switch from a namespace package to a regular package)


@contextlib.contextmanager
def sys_modules_context():
    """
    Make sure sys.modules is the same object and has the same content
    when exiting the context as when entering.

    Similar to importlib.test.util.uncache, but doesn't require explicit
    names.
    """
    sys_modules_saved = sys.modules
    sys_modules_copy = sys.modules.copy()
    try:
        yield
    finally:
        sys.modules = sys_modules_saved
        sys.modules.clear()
        sys.modules.update(sys_modules_copy)


@contextlib.contextmanager
def namespace_tree_context(**kwargs):
    """
    Save import state and sys.modules cache and restore it on exit.
    Typical usage:

    >>> with namespace_tree_context(path=['/tmp/xxyy/portion1',
    ...         '/tmp/xxyy/portion2']):
    ...     pass
    """
    # use default meta_path and path_hooks unless specified otherwise
    kwargs.setdefault('meta_path', sys.meta_path)
    kwargs.setdefault('path_hooks', sys.path_hooks)
    import_context = util.import_state(**kwargs)
    with import_context, sys_modules_context():
        yield

class NamespacePackageTest(unittest.TestCase):
    """
    Subclasses should define self.root and self.paths (under that root)
    to be added to sys.path.
    """
    root = os.path.join(os.path.dirname(__file__), 'namespace_pkgs')

    def setUp(self):
        self.resolved_paths = [
            os.path.join(self.root, path) for path in self.paths
        ]
        self.ctx = namespace_tree_context(path=self.resolved_paths)
        self.ctx.__enter__()

    def tearDown(self):
        # TODO: will we ever want to pass exc_info to __exit__?
        self.ctx.__exit__(None, None, None)


class SingleNamespacePackage(NamespacePackageTest):
    paths = ['portion1']

    def test_simple_package(self):
        import foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        with self.assertRaises(ImportError):
            import foo.two

    def test_module_repr(self):
        import foo.one
        self.assertEqual(repr(foo), "<module 'foo' (namespace)>")


class DynamicPathNamespacePackage(NamespacePackageTest):
    paths = ['portion1']

    def test_dynamic_path(self):
        # Make sure only 'foo.one' can be imported
        import foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

        with self.assertRaises(ImportError):
            import foo.two

        # Now modify sys.path
        sys.path.append(os.path.join(self.root, 'portion2'))

        # And make sure foo.two is now importable
        import foo.two
        self.assertEqual(foo.two.attr, 'portion2 foo two')


class CombinedNamespacePackages(NamespacePackageTest):
    paths = ['both_portions']

    def test_imports(self):
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'both_portions foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')


class SeparatedNamespacePackages(NamespacePackageTest):
    paths = ['portion1', 'portion2']

    def test_imports(self):
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')


class SeparatedOverlappingNamespacePackages(NamespacePackageTest):
    paths = ['portion1', 'both_portions']

    def test_first_path_wins(self):
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')

    def test_first_path_wins_again(self):
        sys.path.reverse()
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'both_portions foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')

    def test_first_path_wins_importing_second_first(self):
        import foo.two
        import foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')


class SingleZipNamespacePackage(NamespacePackageTest):
    paths = ['top_level_portion1.zip']

    def test_simple_package(self):
        import foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        with self.assertRaises(ImportError):
            import foo.two


class SeparatedZipNamespacePackages(NamespacePackageTest):
    paths = ['top_level_portion1.zip', 'portion2']

    def test_imports(self):
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')
        self.assertIn('top_level_portion1.zip', foo.one.__file__)
        self.assertNotIn('.zip', foo.two.__file__)


class SingleNestedZipNamespacePackage(NamespacePackageTest):
    paths = ['nested_portion1.zip/nested_portion1']

    def test_simple_package(self):
        import foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        with self.assertRaises(ImportError):
            import foo.two


class SeparatedNestedZipNamespacePackages(NamespacePackageTest):
    paths = ['nested_portion1.zip/nested_portion1', 'portion2']

    def test_imports(self):
        import foo.one
        import foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')
        fn = os.path.join('nested_portion1.zip', 'nested_portion1')
        self.assertIn(fn, foo.one.__file__)
        self.assertNotIn('.zip', foo.two.__file__)


class LegacySupport(NamespacePackageTest):
    paths = ['not_a_namespace_pkg', 'portion1', 'portion2', 'both_portions']

    def test_non_namespace_package_takes_precedence(self):
        import foo.one
        with self.assertRaises(ImportError):
            import foo.two
        self.assertIn('__init__', foo.__file__)
        self.assertNotIn('namespace', str(foo.__loader__).lower())


class DynamicPathCalculation(NamespacePackageTest):
    paths = ['project1', 'project2']

    def test_project3_fails(self):
        import parent.child.one
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)
        import parent.child.two
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

        self.assertEqual(parent.child.one.attr, 'parent child one')
        self.assertEqual(parent.child.two.attr, 'parent child two')

        with self.assertRaises(ImportError):
            import parent.child.three

        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

    def test_project3_succeeds(self):
        import parent.child.one
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)
        import parent.child.two
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

        self.assertEqual(parent.child.one.attr, 'parent child one')
        self.assertEqual(parent.child.two.attr, 'parent child two')

        with self.assertRaises(ImportError):
            import parent.child.three

        # now add project3
        sys.path.append(os.path.join(self.root, 'project3'))
        import parent.child.three

        # the paths dynamically get longer, to include the new directories
        self.assertEqual(len(parent.__path__), 3)
        self.assertEqual(len(parent.child.__path__), 3)

        self.assertEqual(parent.child.three.attr, 'parent child three')


class ZipWithMissingDirectory(NamespacePackageTest):
    paths = ['missing_directory.zip']

    @unittest.expectedFailure
    def test_missing_directory(self):
        # This will fail because missing_directory.zip contains:
        #   Length      Date    Time    Name
        # ---------  ---------- -----   ----
        #        29  2012-05-03 18:13   foo/one.py
        #         0  2012-05-03 20:57   bar/
        #        38  2012-05-03 20:57   bar/two.py
        # ---------                     -------
        #        67                     3 files

        # Because there is no 'foo/', the zipimporter currently doesn't
        #  know that foo is a namespace package

        import foo.one

    def test_present_directory(self):
        # This succeeds because there is a "bar/" in the zip file
        import bar.two
        self.assertEqual(bar.two.attr, 'missing_directory foo two')


class ModuleAndNamespacePackageInSameDir(NamespacePackageTest):
    paths = ['module_and_namespace_package']

    def test_module_before_namespace_package(self):
        # Make sure we find the module in preference to the
        #  namespace package.
        import a_test
        self.assertEqual(a_test.attr, 'in module')


class ReloadTests(NamespacePackageTest):
    paths = ['portion1']

    def test_simple_package(self):
        import foo.one
        foo = importlib.reload(foo)
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        import foo
        with self.assertRaises(ImportError):
            import foo.two
        foo = importlib.reload(foo)
        with self.assertRaises(ImportError):
            import foo.two

    def test_dynamic_path(self):
        import foo.one
        with self.assertRaises(ImportError):
            import foo.two

        # Now modify sys.path and reload.
        sys.path.append(os.path.join(self.root, 'portion2'))
        foo = importlib.reload(foo)

        # And make sure foo.two is now importable
        import foo.two
        self.assertEqual(foo.two.attr, 'portion2 foo two')


if __name__ == "__main__":
    unittest.main()
