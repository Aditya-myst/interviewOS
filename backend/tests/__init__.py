"""Marks this directory as a regular package.

Without this file `tests/` is only a *namespace* package, and Python keeps looking down
`sys.path` for a real one. Some installed distributions ship their own top-level `tests`
package — bitcoinlib does (it is in `site-packages/tests/`) — and that one wins, so
`from tests.test_planning import ...` resolved to a stranger's test suite and the run died
with `ModuleNotFoundError: No module named 'tests.test_planning'`. It only failed on
machines that had the wrong package installed, which is the worst kind of failure: green
on mine, red on yours.

A regular package found earlier on the path cannot be shadowed this way.
"""
