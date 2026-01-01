"""Tests for safety-net find command handling."""

from .safety_net_test_base import SafetyNetTestCase


class FindDeleteTests(SafetyNetTestCase):
    def test_find_delete_blocked(self) -> None:
        self._assert_blocked(
            'find . -name "*.pyc" -delete',
            "find -delete",
        )

    def test_find_name_argument_delete_allowed(self) -> None:
        self._assert_allowed("find . -name -delete -print")

    def test_find_exec_echo_delete_allowed(self) -> None:
        self._assert_allowed("find . -exec echo -delete \\; -print")

    def test_find_exec_plus_terminator_mentions_delete_allowed(self) -> None:
        self._assert_allowed("find . -exec echo -delete + -print")

    def test_busybox_find_delete_blocked(self) -> None:
        self._assert_blocked(
            'busybox find . -name "*.pyc" -delete',
            "find -delete",
        )

    def test_find_print_allowed(self) -> None:
        self._assert_allowed('find . -name "*.pyc" -print')

    def test_echo_mentions_find_delete_allowed(self) -> None:
        self._assert_allowed('echo "find . -name *.pyc -delete"')

    def test_rg_mentions_find_delete_allowed(self) -> None:
        self._assert_allowed('rg "find .* -delete" file.txt')

    def test_python_c_system_find_delete_blocked(self) -> None:
        self._assert_blocked(
            'python -c "import os; os.system(\\"find . -delete\\")"',
            "find -delete",
        )


class FindExecRmTests(SafetyNetTestCase):
    def test_find_exec_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec rm -rf {} \\;",
            "find -exec rm -rf",
        )

    def test_find_execdir_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find /tmp -execdir rm -rf {} +",
            "find -exec rm -rf",
        )

    def test_find_exec_rm_r_force_blocked(self) -> None:
        self._assert_blocked(
            "find . -name '*.tmp' -exec rm -r --force {} \\;",
            "find -exec rm -rf",
        )

    def test_find_exec_rm_recursive_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec rm --recursive -f {} \\;",
            "find -exec rm -rf",
        )

    def test_find_exec_rm_no_force_allowed(self) -> None:
        self._assert_allowed("find . -exec rm -r {} \\;")

    def test_find_exec_rm_no_recursive_allowed(self) -> None:
        self._assert_allowed("find . -exec rm -f {} \\;")

    def test_find_exec_echo_allowed(self) -> None:
        self._assert_allowed("find . -exec echo {} \\;")

    def test_find_exec_cat_allowed(self) -> None:
        self._assert_allowed("find . -type f -exec cat {} +")

    def test_busybox_find_exec_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "busybox find . -exec rm -rf {} \\;",
            "find -exec rm -rf",
        )

    def test_find_exec_rm_rf_in_bash_c_blocked(self) -> None:
        self._assert_blocked(
            "bash -c 'find . -exec rm -rf {} \\;'",
            "find -exec rm -rf",
        )

    def test_find_exec_env_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec env rm -rf {} ;",
            "find -exec rm -rf",
        )

    def test_find_exec_sudo_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec sudo rm -rf {} ;",
            "find -exec rm -rf",
        )

    def test_find_exec_command_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec command rm -rf {} ;",
            "find -exec rm -rf",
        )

    def test_find_exec_busybox_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find . -exec busybox rm -rf {} ;",
            "find -exec rm -rf",
        )

    def test_find_execdir_env_rm_rf_blocked(self) -> None:
        self._assert_blocked(
            "find /tmp -execdir env rm -rf {} +",
            "find -exec rm -rf",
        )
