import re
from typing import Optional
from app import messages


INPUT_PARSE_PATTERNS = (
    'System.Int32.Parse',
    'System.Int64.Parse',
    'System.Double.Parse',
    'System.Decimal.Parse',
    'System.Convert.ToInt32',
    'System.Convert.ToInt64',
    'System.Convert.ToDouble',
    'System.Convert.ToDecimal',
)

TIMEOUT_PATTERNS = (
    'Terminated',
    'timed out',
)


def clean_str(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        return value.replace('\r', '').rstrip('\n')
    return value


def clean_error(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        value = clean_str(value)

        value = re.sub(
            pattern='\/(tmp|sandbox)\/\S*\.cs',
            repl='main.cs',
            string=value
        )

        if any(x in value for x in TIMEOUT_PATTERNS):
            value = messages.MSG_1

        elif (
            'System.ArgumentNullException' in value and
            'Parameter name: s' in value and
            any(x in value for x in INPUT_PARSE_PATTERNS)
        ):
            value = messages.MSG_8

        elif 'the monitored command dumped core' in value:
            value = clean_str(
                re.sub(
                    pattern=r'(?im)^.*the monitored command dumped core.*$',
                    repl='',
                    string=value
                )
            )

    return value or None