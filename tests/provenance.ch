module Shoreleave.Tests.Provenance
import Shoreleave.Provenance (shoreleave_version)
import Std.Test (assert_eq, assert_true)
def test_exported_package_version() -> unit ! { Test } = assert_eq(shoreleave_version(), "0.1.4", "exported package version")
def test_exported_version_is_not_previous_release() -> unit ! { Test } = assert_true(not(eq(shoreleave_version(), "0.1.3")), "previous package version is not advertised")
