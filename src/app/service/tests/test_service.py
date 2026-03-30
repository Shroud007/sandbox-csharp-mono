import pytest
from unittest.mock import call

from app import messages
from app.entities import (
    DebugData,
    TestData,
    TestsData,
)
from app.service import exceptions
from app.service.entities import (
    CSharpFile,
    ExecuteResult,
)
from app.service.exceptions import CheckerException
from app.service.main import CSharpService


def test_execute__console_result__ok():
    data_in = '2 3'
    code = (
        'using System;\n'
        'class Program\n'
        '{\n'
        '    static void Main()\n'
        '    {\n'
        '        var parts = Console.ReadLine().Split();\n'
        '        int a = int.Parse(parts[0]);\n'
        '        int b = int.Parse(parts[1]);\n'
        '        Console.WriteLine(a + b);\n'
        '    }\n'
        '}\n'
    )
    file = CSharpFile(code)
    CSharpService._compile(file)

    exec_result = CSharpService._execute(file=file, data_in=data_in)

    assert exec_result.result == '5'
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():
    code = (
        'using System;\n'
        'class Program\n'
        '{\n'
        '    static void Main()\n'
        '    {\n'
        '    }\n'
        '}\n'
    )
    file = CSharpFile(code)
    CSharpService._compile(file)

    exec_result = CSharpService._execute(file=file)

    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__timeout__return_error(mocker):
    code = (
        'using System;\n'
        'class Program\n'
        '{\n'
        '    static void Main()\n'
        '    {\n'
        '        while (true) {}\n'
        '    }\n'
        '}\n'
    )
    file = CSharpFile(code)
    CSharpService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    execute_result = CSharpService._execute(file=file)

    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_compile__invalid_syntax__return_error():
    code = (
        'using System;\n'
        'class Program\n'
        '{\n'
        '    static void Main()\n'
        '    {\n'
        '        Console.WriteLine("Hello")\n'
        '    }\n'
        '}\n'
    )
    file = CSharpFile(code)

    compile_error = CSharpService._compile(file)

    assert compile_error is not None
    assert 'main.cs' in compile_error
    assert 'error CS' in compile_error
    file.remove()


def test_check__true__ok():
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    check_result = CSharpService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value,
    )

    assert check_result is True


def test_check__false__ok():
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    check_result = CSharpService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value,
    )

    assert check_result is False


def test_check__invalid_checker_func__raise_exception():
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:\n'
        '    return right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        CSharpService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    result = right_value == value'
    )

    with pytest.raises(CheckerException) as ex:
        CSharpService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    return None'
    )

    with pytest.raises(CheckerException) as ex:
        CSharpService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:\n'
        '    include(invalid syntax here)\n'
        '    return True'
    )

    with pytest.raises(CheckerException) as ex:
        CSharpService._check(
            checker_func=checker_func,
            right_value='value',
            value='value',
        )

    assert ex.value.message == messages.MSG_5
    assert ex.value.details == "invalid syntax. Perhaps you forgot a comma? (<string>, line 2)"


def test_debug__compile_is_success__ok(mocker):
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(CSharpFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.CSharpService._compile',
        return_value=None,
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some runtime error',
    )
    execute_mock = mocker.patch(
        'app.service.main.CSharpService._execute',
        return_value=execute_result,
    )
    data = DebugData(code='some code', data_in='some data_in')

    debug_result = CSharpService.debug(data)

    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(file=file_mock, data_in=data.data_in)
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):
    compile_error = 'some error'
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(CSharpFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.CSharpService._compile',
        return_value=compile_error,
    )
    execute_mock = mocker.patch('app.service.main.CSharpService._execute')
    data = DebugData(code='some code', data_in='some data_in')

    debug_result = CSharpService.debug(data)

    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(CSharpFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.CSharpService._compile',
        return_value=None,
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some runtime error',
    )
    execute_mock = mocker.patch(
        'app.service.main.CSharpService._execute',
        return_value=execute_result,
    )
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.CSharpService._check',
        return_value=check_result,
    )
    test_1 = TestData(data_in='some test input 1', data_out='some test out 1')
    test_2 = TestData(data_in='some test input 2', data_out='some test out 2')
    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2],
    )

    testing_result = CSharpService.testing(data)

    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list == [
        call(file=file_mock, data_in=test_1.data_in),
        call(file=file_mock, data_in=test_2.data_in),
    ]
    assert check_mock.call_args_list == [
        call(
            checker_func=data.checker,
            right_value=test_1.data_out,
            value=execute_result.result,
        ),
        call(
            checker_func=data.checker,
            right_value=test_2.data_out,
            value=execute_result.result,
        ),
    ]
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(CSharpFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    compile_mock = mocker.patch(
        'app.service.main.CSharpService._compile',
        return_value=compile_error,
    )
    execute_mock = mocker.patch('app.service.main.CSharpService._execute')
    check_mock = mocker.patch('app.service.main.CSharpService._check')
    test_1 = TestData(data_in='some test input 1', data_out='some test out 1')
    test_2 = TestData(data_in='some test input 2', data_out='some test out 2')
    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2],
    )

    testing_result = CSharpService.testing(data)

    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result is None
    assert tests_result[0].error == compile_error
    assert tests_result[0].ok is False
    assert tests_result[1].result is None
    assert tests_result[1].error == compile_error
    assert tests_result[1].ok is False
